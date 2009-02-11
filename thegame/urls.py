from django.conf.urls.defaults import *

urlpatterns = patterns('financegame.thegame.views',
    (r'^$', 'index'),
    
    (r'^userprofile/$', 'user_profile'),
    (r'^userprofile/edit/$', 'user_profile_edit'),
    
    (r'^about/$', 'about'),
    (r'^help/$', 'help'),
    (r'^contact/$', 'contact'),
    (r'^contacted/$', 'contacted'),
    
    (r'^worlds/$', 'world_list'),
    
    (r'^worlds/(?P<world_id>\d+)/$', 'world_detail'),
    (r'^worlds/(?P<world_id>\d+)/(?P<period_id>\d+)/$', 'period_detail'),
    (r'^worlds/(?P<world_id>\d+)/(?P<period_id>\d+)/period_results/$', 'period_results'),
    (r'^auctions/(?P<auction_id>\d+)/$', 'auction_detail'),
    (r'^auctions/(?P<auction_id>\d+)/bid_history/$', 'bid_history'),
    
    
    (r'^worlds/(?P<world_id>\d+)/master/$', 'world_detail_master'), # home for mastering a world
    (r'^worlds/(?P<world_id>\d+)/(?P<period_id>\d+)/master/$', 'period_detail_master'), # master a period
    (r'^worlds/(?P<world_id>\d+)/(?P<period_id>\d+)/period_results/master/$', 'period_results_master'), 
    (r'^auctions/(?P<auction_id>\d+)/master/$', 'auction_detail_master'), # master an asset/auction
    (r'^auctions/(?P<auction_id>\d+)/bid_history/master/$', 'bid_history_master'), # master bid history
    
    #~ (r'^(?P<poll_id>\d+)/$', 'detail'),
    #~ (r'^(?P<poll_id>\d+)/results/$', 'results'),
    #~ (r'^(?P<poll_id>\d+)/vote/$', 'vote'),
)
