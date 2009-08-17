from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

#import settings

import datetime

# Create your models here.
class World(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    initial_wealth = models.FloatField("Initial user wealth.", default=100000.0)
    lone_bidder_profit = models.FloatField("Default lone bidder profit", default=100000.0)
    default_nobid_error = models.FloatField("Default no-bid error", default=100000.0)
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.world_detail', (), {'world_id': self.id})
    
    def user_is_master(self, user):
        '''Return true if the supplied user object is a master of this world.'''
        try:
            self.mastered_worlds.get(user__id = user.id)
            return True
        except ObjectDoesNotExist:
            return False
    
    def __unicode__(self):
        return u'%s' % self.name

class PeriodSummary(models.Model):
    user = models.ForeignKey(User)
    period = models.ForeignKey('Period')
    starting_wealth = models.FloatField()
    ending_wealth = models.FloatField()
    wealth_created = models.FloatField()
    period_return = models.FloatField()
    auctions_won = models.IntegerField(default=0)
    bids_placed = models.IntegerField(default=0)
    mean_absolute_error = models.FloatField()
        
    def __unicode__(self):
        return u'%s: %s: %s' % (self.user.username, self.period.number, self.period_return)

class Period(models.Model):
    world = models.ForeignKey(World)
    number = models.IntegerField()
    name = models.CharField(max_length=200)
    description = models.TextField()
    risk_free_rate = models.FloatField()
    start_time = models.DateTimeField('Period Start Time')
    end_time = models.DateTimeField('Period End Time')
    summary_completed = models.BooleanField(default=False)
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.period_detail', (), {'world_id':self.world.id, 'period_id':self.id})
    
    def is_started(self):
        '''True if period is started.'''
        return self.start_time < datetime.datetime.now()
        
    def is_ended(self):
        '''True if period is ended.'''
        return self.end_time < datetime.datetime.now()
        
    def get_period_status(self):
        if self.is_started() and not self.is_ended():
            return "In progress"
        elif not self.is_started():
            return "Not started"
        elif self.is_ended():
            return "Ended"
        
    def calc_period_summary(self):
        ''' for the period, get a list of (user, period, initial wealth, final wealth, return), and create periodsummary objects
        
        we call this every time a user views profile, so it's generated if it doesn't exist, otherwise does nothing.'''
    
        if not self.summary_completed and self.is_ended():
            self.summary_completed = True #set the flag right away, so that we don't attempt to do this again.
            self.save()
            membership_list = self.world.membership_set.all()
            for membership in membership_list:
                auctions_won = 0
                initial_wealth = membership.wealth
                final_wealth = initial_wealth
                error_list = []
                for asset in self.asset_set.all():
                    try:
                        asset.auction.winning_bid_set.get(bidder__id = membership.user.user.id)
                        num_winners = asset.auction.winning_bid_set.count()
                        final_wealth = final_wealth - asset.auction.final_price/num_winners + asset.true_value/num_winners
                        auctions_won = auctions_won + 1
                    except ObjectDoesNotExist:
                        pass # didn't win this auction.
                        
                    try:
                        bid = asset.auction.bid_set.get(bidder__id = membership.user.user.id)
                        error_list.append(abs(bid.amount - asset.true_value))
                    except ObjectDoesNotExist:
                        error_list.append(self.world.default_nobid_error)
                
                membership.wealth = final_wealth
                membership.save()
                
                bids_placed = Bid.objects.filter(bidder = membership.user.user, auction__asset__period = self).count()
                
                ps = PeriodSummary(user = membership.user.user, period = self, starting_wealth = initial_wealth, ending_wealth = final_wealth, wealth_created = (final_wealth - initial_wealth), period_return = (final_wealth/initial_wealth - 1)*100.0, auctions_won = auctions_won, bids_placed = bids_placed, mean_absolute_error = (sum(error_list)/float(len(error_list))))
                ps.save()
            
            return ''
        else:
            return ''
    
    def recalc_period_summary(self, reset_world_wealth=False):
        ''' recalculate period summary results.
        
        this is to be used in case any asset values are updated after period summaries are over, etc.
        
        calculates returns and wealth using previous period's ending_wealth (or, for 1st period, default world starting wealth)
        '''
        periodsummaries = self.periodsummary_set.all()
        if reset_world_wealth:
            membership_list = self.world.membership_set.all()
        if self.number > 1:
            previousperiodsummaries = self.world.period_set.get(number=self.number -1).periodsummary_set.all()
        else:
            previousperiodsummaries = None
        
        for summary in periodsummaries:
            auctions_won = 0
            
            if previousperiodsummaries:
                initial_wealth = previousperiodsummaries.get(user = summary.user).ending_wealth
            else:
                initial_wealth = self.world.initial_wealth
                
            final_wealth = initial_wealth
            
            error_list = []
            
            for asset in self.asset_set.all():
                try:
                    asset.auction.winning_bid_set.get(bidder__id = summary.user.id)
                    num_winners = asset.auction.winning_bid_set.count()
                    final_wealth = final_wealth - asset.auction.final_price/num_winners + asset.true_value/num_winners
                    auctions_won = auctions_won + 1
                except ObjectDoesNotExist:
                    pass # didn't win this auction.
                    
                try:
                    bid = asset.auction.bid_set.get(bidder__id = summary.user.id)
                    error_list.append(abs(bid.amount - asset.true_value))
                except ObjectDoesNotExist:
                    error_list.append(self.world.default_nobid_error)
            
            bids_placed = Bid.objects.filter(bidder = summary.user, auction__asset__period = self).count()
            
            summary.starting_wealth = initial_wealth
            summary.ending_wealth = final_wealth
            summary.wealth_created = (final_wealth - initial_wealth)
            summary.period_return = (final_wealth/initial_wealth - 1)*100.0
            summary.auctions_won = auctions_won
            summary.bids_placed = bids_placed
            summary.mean_absolute_error = sum(error_list)/float(len(error_list))
            
            summary.save()
            
            if reset_world_wealth:
                membership = membership_list.get(user__user = summary.user)
                membership.wealth = final_wealth
                membership.save()
            
        return ''    
    
    def __unicode__(self):
        return u'%s: %s: %s' % (self.world.name, self.number, self.name)

class Asset(models.Model):
    period = models.ForeignKey(Period)
    name = models.CharField(max_length=200)
    description = models.TextField()
    true_value = models.FloatField()
    
    def __unicode__(self):
        return u'Period %s, %s: Asset %s' % (self.period.number, self.period.name, self.name)
    
class Auction(models.Model):
    asset = models.OneToOneField(Asset)
    final_price = models.FloatField(null=True, blank=True)
    result_completed = models.BooleanField(default=False)
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.auction_detail',(),{'auction_id':self.id})
    
    def is_ended(self):
        return self.asset.period.is_ended()
        
    def get_end_time(self):
        return self.asset.period.end_time
    
    def get_start_time(self):
        return self.asset.period.start_time
    
    def did_user_bid(self, user):
        try:
            user_bid = self.bid_set.get(bidder__id = user.id)
            return user_bid
        except ObjectDoesNotExist:
            return False
        
    def calc_result(self):
        if not self.result_completed and self.is_ended():
            self.result_completed = True #set the flag right away, so that we don't attempt to do this again.
            self.save()
            sorted_bids = self.bid_set.order_by('-amount')
            if sorted_bids.count() >= 2:
                if sorted_bids[0].amount > sorted_bids[1].amount:
                    # we have one winner, simple.
                    bid = sorted_bids[0]
                    bid.winner_of = self
                    bid.save()
                    self.final_price = sorted_bids[1].amount
                else:
                    winning_bids = sorted_bids.filter(amount = sorted_bids[0].amount)
                    for bid in winning_bids:
                        bid.winner_of = self
                        bid.save()
                    self.final_price = sorted_bids[0].amount
                self.save()
            elif sorted_bids.count() == 1:
                bid = sorted_bids[0]
                bid.winner_of = self
                bid.save()
                self.final_price = sorted_bids[0].amount - self.asset.period.world.lone_bidder_profit
                self.save()
                
            return ''
        else:
            return ''
    
    def __unicode__(self):
        return u'%s: %s: %s: %s' % (self.asset.period.world.name, self.asset.period.name, self.asset.name, self.final_price)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    mastered_worlds = models.ManyToManyField(World, related_name='mastered_worlds', null=True, blank=True)
    world_memberships = models.ManyToManyField(World, related_name='member_worlds', through='Membership')
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.user_profile',(),{})

    def __unicode__(self):
        return u'%s: %s, %s' % (self.user.username, self.user.last_name,
                    self.user.first_name)

class Membership(models.Model):
    user = models.ForeignKey(UserProfile)
    world = models.ForeignKey(World)
    wealth = models.FloatField()
    approved = models.BooleanField(default=False)
        
    def __unicode__(self):
        return u'%s, %s' % (self.user.user.username, self.world.name)

class Bid(models.Model):
    auction = models.ForeignKey(Auction)
    winner_of = models.ForeignKey(Auction, related_name='winning_bid_set', null=True, blank=True)
    bidder = models.ForeignKey(User)
    amount = models.FloatField()
    time = models.DateTimeField('Bid Time')
    
    def __unicode__(self):
        return u'%s: %s: %s' % (self.auction.asset.name, self.bidder.username, self.amount)


    
