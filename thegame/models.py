from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

#import settings

import datetime

# Create your models here.
class World(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    #initial_wealth = models.FloatField("Initial user wealth.", default=100000.0)
    #lone_bidder_profit = models.FloatField("Default lone bidder profit", default=100000.0)
    #default_nobid_error = models.FloatField("Default no-bid error", default=100000.0)
    #grade_scale_max = models.FloatField("Grade scale maximum", default=100.0)
    #grade_scale_min = models.FloatField("Grade scale minimum", default=20.0)
    correct_tolerance = models.FloatField("Tolerance for correct answer, percent", default=1.0)
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.world_detail', (), {'world_id': self.id})
    
    def user_is_master(self, user):
        '''Return true if the supplied user object is a master of this world.'''
        try:
            membership = user.get_profile().membership_set.get(world=self)
            if membership.is_master:
                return True
            else:
                return False
        except ObjectDoesNotExist:
            return False
    
    def user_is_member(self, user):
        '''Test if user is member of world and is approved.'''
        try:
            membership = user.get_profile().membership_set.get(world=self)
            if membership.approved:
                return membership
            else:
                return False
        except ObjectDoesNotExist:
            return False
    
    def __unicode__(self):
        return u'%s' % self.name

class PeriodSummary(models.Model):
    user = models.ForeignKey(User)
    period = models.ForeignKey('Period')
    #wealth_created = models.FloatField()
    #auctions_won = models.IntegerField(default=0)
    bids_placed = models.IntegerField(default=0)
    #mean_absolute_error = models.FloatField()
    #grade_wealth = models.FloatField(null=True, blank=True)
    #grade_error = models.FloatField(null=True, blank=True)
    correct_count = models.IntegerField(null=True, blank=True)
        
    def __unicode__(self):
        return u'%s: %s: %s' % (self.user.username, self.period.number, self.correct_count)

class Period(models.Model):
    world = models.ForeignKey(World)
    number = models.IntegerField()
    name = models.CharField(max_length=200)
    description = models.TextField()
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
        
    def calc_period_summary(self, force=False, recalc_auctions=False):
        '''Create periodsummary objects for each user for the period.
        
        These objects get created once the period is over, and contain some
        summary statistics, namely:
        - bids placed
        - correct count
        
        Currently we call this every time a user views profile, or period 
        detail, so it's generated if it doesn't exist, otherwise does nothing.
        
        Ideally, these should only be generated once, by a cron job or 
        something like that. 
        
        If the argument 'force' is true, will recalculate summaries even if
        one has been calculated before. This feature would be used by an admin
        in case asset values get changed retroactively, etc.
        '''
    
        if (not self.summary_completed or force) and (self.is_ended()):
            self.summary_completed = True #set the flag right away, so that we don't attempt to do this again.
            self.save()
            membership_list = self.world.membership_set.all()
                            
            for membership in membership_list:
                if membership.is_master:
                    continue # world masters don't get results
                if not membership.approved:
                    continue # unapproved members don't get results, either
                correct_count = 0
                for asset in self.asset_set.all():                        
                    try:
                        bid = asset.auction.bid_set.get(bidder__id = membership.user.user.id)
                        correct_flag = (abs(bid.amount - asset.true_value) < abs(self.world.correct_tolerance / 100.0 * asset.true_value))
                        correct_count += int(correct_flag)
                    except ObjectDoesNotExist:
                        pass
                
                bids_placed = Bid.objects.filter(bidder = membership.user.user, auction__asset__period = self).count()
                
                try:
                    ps = self.periodsummary_set.get(user = membership.user.user)
                    ps.bids_placed = bids_placed
                    ps.correct_count = correct_count
                    ps.save()
                except ObjectDoesNotExist:
                    ps = PeriodSummary(user = membership.user.user, 
                            period = self, 
                            bids_placed = bids_placed, 
                            correct_count = correct_count)
                    ps.save()
            
            return ''
        else:
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
    #final_price = models.FloatField(null=True, blank=True)
    #result_completed = models.BooleanField(default=False)
    
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
            
    def __unicode__(self):
        return u'%s: %s: %s: %s' % (self.asset.period.world.name, self.asset.period.name, self.asset.name, self.final_price)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.user_profile',(),{})

    def __unicode__(self):
        return u'%s: %s, %s' % (self.user.username, self.user.last_name,
                    self.user.first_name)

class Membership(models.Model):
    user = models.ForeignKey(UserProfile)
    world = models.ForeignKey(World)
    #wealth = models.FloatField()
    approved = models.BooleanField(default=False)
    is_master = models.BooleanField(default=False)
        
    def __unicode__(self):
        return u'%s, %s' % (self.user.user.username, self.world.name)

class Bid(models.Model):
    auction = models.ForeignKey(Auction)
    #winner_of = models.ForeignKey(Auction, related_name='winning_bid_set', null=True, blank=True)
    bidder = models.ForeignKey(User)
    amount = models.FloatField()
    time = models.DateTimeField('Bid Time')
    
    def __unicode__(self):
        return u'%s: %s: %s' % (self.auction.asset.name, self.bidder.username, self.amount)

