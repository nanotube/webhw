from financegame.thegame.models import World, Period, Asset, UserProfile, Membership, Auction, Bid, PeriodSummary
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

class PeriodInline(admin.StackedInline):
    model = Period
    extra = 3

class MembershipInline(admin.StackedInline):
    model = Membership
    extra = 1

class AssetInline(admin.StackedInline):
    model = Asset
    extra = 3

class UserProfileInline(admin.StackedInline):
    model=UserProfile
    fk_name = 'user'
    max_num=1

class AuctionInline(admin.StackedInline):
    model=Auction
    max_num = 1

class BidInline1(admin.StackedInline):
    model=Bid
    fk_name = 'auction'
    extra=1

#class BidInline2(admin.StackedInline):
    #model=Bid
    #fk_name = 'winner_of'
    #verbose_name_plural = 'Winning Bids'
    #extra = 1
    
class PeriodSummaryInline(admin.StackedInline):
    model=PeriodSummary
    extra = 1

class WorldAdmin(admin.ModelAdmin):
    #fields = ['name','description']
    inlines = [PeriodInline, MembershipInline]
    search_fields = ['name']
   
class PeriodAdmin(admin.ModelAdmin):
    inlines = [AssetInline, PeriodSummaryInline]
    list_display = ('name', 'number', 'get_world')
    search_fields = ('name', 'world__name')
    
    def get_world(self, obj):
        return unicode(obj.world.name)
    get_world.short_description = "World"
    
class MyUserAdmin(UserAdmin):
    inlines = [UserProfileInline, ]
    list_display = UserAdmin.list_display + ('is_active',)
    list_editable = ('email', 'first_name', 'last_name', 'is_active')

class UserProfileAdmin(admin.ModelAdmin):
    inlines = [MembershipInline,]
    list_display = ('get_username', 'get_first_name', 'get_last_name',)
    search_fields = ('user__name', 'user__first_name', 'user__last_name',)
    
    def get_username(self, obj):
        return unicode(obj.user.username)
    get_username.short_description = "User"
    
    def get_first_name(self, obj):
        return unicode(obj.user.first_name)
    get_first_name.short_description = "First Name"
    
    def get_last_name(self, obj):
        return unicode(obj.user.last_name)
    get_last_name.short_description = "Last Name"
    
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_first_name', 'get_last_name', 'get_world', 'approved', )
    search_fields = ('user__username', 'world__name', )
    list_filter = ('approved', )
    
    def get_world(self, obj):
        return unicode(obj.world.name)
    get_world.short_description = "World"
    
    def get_username(self, obj):
        return unicode(obj.user.user.username)
    get_username.short_description = "User"
    
    def get_first_name(self, obj):
        return unicode(obj.user.user.first_name)
    get_first_name.short_description = "First Name"
    
    def get_last_name(self, obj):
        return unicode(obj.user.user.last_name)
    get_last_name.short_description = "Last Name"

class AssetAdmin(admin.ModelAdmin):
    inlines = [AuctionInline, ]
    list_display = ('name', 'get_world', 'get_period')
    search_fields = ('name', 'period__name', 'period__world__name')
    
    def get_world(self, obj):
        return unicode(obj.period.world.name)
    get_world.short_description = "World"
    
    def get_period(self, obj):
        return "%s: %s" %(obj.period.number, obj.period.name)
    get_period.short_description = "Period"

class AuctionAdmin(admin.ModelAdmin):
    inlines = [BidInline1, ]#BidInline2,]
    list_display = ('get_asset_name', 'get_world', 'get_period')
    search_fields = ('asset__name', 'asset__period__name', 'asset__period__world__name')
    
    def get_asset_name(self, obj):
        return unicode(obj.asset.name)
    get_asset_name.short_description = "Asset"
    
    def get_world(self, obj):
        return unicode(obj.asset.period.world.name)
    get_world.short_description = "World"
    
    def get_period(self, obj):
        return "%s: %s" %(obj.asset.period.number, obj.asset.period.name)
    get_period.short_description = "Period"

    
class BidAdmin(admin.ModelAdmin):
    list_display = ('get_asset_name', 'amount', 'get_username', 'get_world', 'get_period')
    search_fields = ('auction__asset__name', 'bidder__username', 'auction__asset__period__name', 'auction__asset__period__world__name')
     
    def get_username(self, obj):
        return unicode(obj.bidder.username)
    get_username.short_description = "Bidder"
    
    def get_asset_name(self, obj):
        return unicode(obj.auction.asset.name)
    get_asset_name.short_description = "Asset"
    
    def get_world(self, obj):
        return unicode(obj.auction.asset.period.world.name)
    get_world.short_description = "World"
    
    def get_period(self, obj):
        return "%s: %s" %(obj.auction.asset.period.number, obj.auction.asset.period.name)
    get_period.short_description = "Period"

class PeriodSummaryAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_world', 'get_period', 'correct_count')
    search_fields = ('user__username', 'period__name', 'period__world__name')
    
    def get_username(self, obj):
        return unicode(obj.user.username)
    get_username.short_description = "User"
    
    def get_world(self, obj):
        return unicode(obj.period.world.name)
    get_world.short_description = "World"
    
    def get_period(self, obj):
        return "%s: %s" %(obj.period.number, obj.period.name)
    get_period.short_description = "Period"


admin.site.register(World, WorldAdmin)
admin.site.register(Period, PeriodAdmin)

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Membership, MembershipAdmin)

admin.site.register(Asset, AssetAdmin)
admin.site.register(Auction, AuctionAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(PeriodSummary, PeriodSummaryAdmin)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
