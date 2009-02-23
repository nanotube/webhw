from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

#import settings

import datetime

# Create your models here.
class World(models.Model):
    name = models.CharField(max_length=200)
    #pub_date = models.DateTimeField('date published')
    description = models.TextField()
    minimum_bid_increment = models.DecimalField("Minimum Bid Increment", default=1.0, max_digits=10, decimal_places=2)
    maximum_auction_end_time_offset = models.FloatField("Maximum auction end time offset, in hours", default=2.0)
    auction_end_time_offset_per_bid = models.FloatField("Auction extension per bid, in minutes", default=5.0)
    initial_wealth = models.FloatField("Initial user wealth.", default=100000.0)
    
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
    period_return = models.FloatField()
    auctions_won = models.IntegerField(default=0)
    bids_placed = models.IntegerField(default=0)
    auctions_bid_on = models.IntegerField(default=0)
    
    def __unicode__(self):
        return u'%s: %s: %s' % (self.user.username, self.period.number, self.period_return)

class Period(models.Model):
    world = models.ForeignKey(World)
    number = models.IntegerField()
    name = models.CharField(max_length=200)
    description = models.TextField()
    #viewable = models.BooleanField()
    risk_free_rate = models.FloatField()
    start_time = models.DateTimeField('Period Start Time')
    end_time = models.DateTimeField('Period End Time')
    summary_completed = models.BooleanField(default=False)
    #votes = models.IntegerField()
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.period_detail', (), {'world_id':self.world.id, 'period_id':self.id})
    
    def is_started(self):
        return self.start_time < datetime.datetime.now()
        
    def is_ended(self):
        '''Determine if period is ended. 
        
        If it is now past max end time, it's ended
        If it is now before min end time, it's not ended
        Otherwise, check all auctions individually, and if they are all ended, period is ended.'''
        
        if self.end_time + datetime.timedelta(hours=self.world.maximum_auction_end_time_offset) < datetime.datetime.now():
            return True
        if self.end_time > datetime.datetime.now():
            return False
        
        all_auctions_ended = True
        for asset in self.asset_set.all():
            if not asset.auction.is_ended():
                all_auctions_ended = False
                
        return all_auctions_ended
        
    def get_period_status(self):
        if self.is_started() and not self.is_ended():
            return "In progress"
        elif not self.is_started():
            return "Not started"
        elif self.is_ended():
            return "Ended"
            
        #~ if self.start_time < datetime.datetime.now() and datetime.datetime.now() < self.end_time + datetime.timedelta(hours=self.world.maximum_auction_end_time_offset):
            #~ status='In progress'
        #~ elif self.start_time > datetime.datetime.now():
            #~ status='Not started'
        #~ elif datetime.datetime.now() > self.end_time + datetime.timedelta(hours=self.world.maximum_auction_end_time_offset):
            #~ status='Ended'
        #~ return status
    
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
                for asset in self.asset_set.all():
                    if asset.auction.high_bid is not None and asset.auction.high_bid.bidder.id == membership.user.user.id:
                        final_wealth = final_wealth - asset.auction.current_price + asset.true_value
                        auctions_won = auctions_won + 1
                
                membership.wealth = final_wealth
                membership.save()
                
                bids_placed = Bid.objects.filter(bidder = membership.user.user, auction__asset__period = self)
                auctions_bid_on = bids_placed.values('auction').distinct().count()
                bids_placed = bids_placed.count()
                
                ps = PeriodSummary(user = membership.user.user, period = self, starting_wealth = initial_wealth, ending_wealth = final_wealth, period_return = (final_wealth/initial_wealth - 1)*100.0, auctions_won = auctions_won, bids_placed = bids_placed, auctions_bid_on = auctions_bid_on)
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
    current_price = models.FloatField(null=True, blank=True)
    starting_bid = models.FloatField()
    #start_time = models.DateTimeField('Auction Start Time')
    #initial_end_time = models.DateTimeField('Initial Auction End Time')
    end_time = models.DateTimeField('Current Auction End Time', null=True, blank=True)
    max_end_time = models.DateTimeField('Auction Max End Time', null=True, blank=True)
    high_bid = models.OneToOneField('Bid', related_name='high_bid', null=True, blank=True)
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.auction_detail',(),{'auction_id':self.id})
    
    def is_ended(self):
        return self.get_current_end_time() < datetime.datetime.now()
    
    def minimum_bid(self):
        if self.bid_set.count() > 0:
            minimum_bid = self.current_price + self.asset.period.world.minimum_bid_increment
        else:
            minimum_bid = self.starting_bid
        return minimum_bid

    def get_max_end_time(self):
        if self.max_end_time is None:
            td = datetime.timedelta(hours=self.asset.period.world.maximum_auction_end_time_offset)
            self.max_end_time = self.asset.period.end_time + td
            self.save()
        return self.max_end_time
        #~ td = datetime.timedelta(hours=self.asset.period.world.maximum_auction_end_time_offset)
        #~ max_end_time = self.asset.period.end_time + td
        #~ return max_end_time
    
    def get_current_end_time(self):
        #~ if self.end_time is None:
            #~ self.end_time = self.asset.period.end_time
            #~ self.save()
        #~ return self.end_time
        if self.end_time is None:
            end_time = self.asset.period.end_time
        else:
            end_time = self.end_time
        return end_time

    
    def get_start_time(self):
        return self.asset.period.start_time
    
    def get_current_price(self):
        if self.bid_set.count() > 0:
            cur_price = self.current_price
        else:
            cur_price = self.starting_bid
        return cur_price
    
    def __unicode__(self):
        return u'%s: %s' % (self.asset.name, self.current_price)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    mastered_worlds = models.ManyToManyField(World, related_name='mastered_worlds', null=True, blank=True)
    world_memberships = models.ManyToManyField(World, related_name='member_worlds', through='Membership')
    #wealth = models.FloatField()
    description = models.CharField(max_length=200, null=True, blank=True)
    #~ def get_current_wealth(self):
        #~ self.user.membership_set.filter(
    
    @models.permalink
    def get_absolute_url(self):
        return ('financegame.thegame.views.user_profile',(),{})

    def __unicode__(self):
        return u'%s' % (self.user.username)

class Membership(models.Model):
    user = models.ForeignKey(UserProfile)
    world = models.ForeignKey(World)
    wealth = models.FloatField()
    approved = models.BooleanField(default=False)
    
    #~ @models.permalink
    #~ def get_absolute_url(self):
        #~ return self.world.get_absolute_url() + 'membership/' + unicode(self.id) + '/'
    
    def __unicode__(self):
        return u'%s, %s' % (self.user.user.username, self.world.name)

class Bid(models.Model):
    auction = models.ForeignKey(Auction)
    bidder = models.ForeignKey(User)
    amount = models.FloatField()
    time = models.DateTimeField('Bid Time')
    
    def get_amount_display_value(self):
        '''Truncate bid amount to auction current price
        
        If bid amount is higher than auction current price (i.e. it is the high bidder's maximum bid,
        then for display purposes the bid amount should be capped at the auction's current price
        so as not to reveal the private maximum value of the bidder.
        '''
        if self.amount > self.auction.get_current_price():
            return self.auction.get_current_price()
        else:
            return self.amount
            
    def display_truncated(self):
        '''decide if bid amount needs to be truncated'''
        if self.amount > self.auction.get_current_price() or self.id == self.auction.high_bid.id:
            return True
        else:
            return False
    
    def __unicode__(self):
        return u'%s: %s: %s' % (self.auction.asset.name, self.bidder.username, self.amount)


    