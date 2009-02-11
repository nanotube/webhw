from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout
#from django.views.generic.simple import redirect_to

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^financegame/', include('financegame.foo.urls')),
    (r'^thegame/', include('financegame.thegame.urls')),
    (r'^$', include('financegame.thegame.urls')),
    
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'thegame/media'}),
    
    (r'^accounts/$',  'django.views.generic.simple.redirect_to', {'url': '/accounts/login/'}),
    (r'^accounts/login/$',  'financegame.thegame.views.login', {'template_name': 'registration/login.html'}),
    (r'^accounts/logout/$', logout, {'template_name': 'registration/logout.html'}),
    (r'^accounts/create_account/$',  'financegame.thegame.views.create_account', {'template_name': 'registration/create_account.html'}),
    (r'^accounts/account_created/$',  'financegame.thegame.views.account_created', {'template_name': 'registration/account_created.html'}),
    
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
