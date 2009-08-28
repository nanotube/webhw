# Create your views here.
import datetime
#import settings

from django.views.generic.simple import redirect_to
#from django.contrib.auth.views import login as generic_login
from auth_views import login as generic_login
from django.contrib.auth.views import logout as generic_logout

from financegame.thegame.models import World, Period, Auction, Bid, UserProfile, Membership
from financegame.thegame.forms import (UserCreationForm, ContactForm, 
        WorldForm, AuctionForm, AssetForm, PeriodForm, 
        RecalculatePeriodResultsForm, MembershipFormSet)
from django.contrib.auth.models import User

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.mail import send_mail

from django.core.exceptions import ObjectDoesNotExist

def index(request):
    if request.user.is_authenticated():
        return redirect_to(request, url ='/thegame/userprofile/')
    else:
        return generic_login(request)

def about(request):
    return render_to_response('about.html', {}, context_instance=RequestContext(request))

def help(request):
    return render_to_response('help.html', {}, context_instance=RequestContext(request))

def contact(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ContactForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender = form.cleaned_data['sender']
            cc_myself = form.cleaned_data['cc_myself']

            recipients = ['dfolkins@gmail.com']
            if cc_myself:
                recipients.append(sender)
            
            send_mail(subject, message, sender, recipients)
            return HttpResponseRedirect('/thegame/contacted/') # Redirect after POST
    else:
        form = ContactForm() # An unbound form

    return render_to_response('contact.html', {'form': form,}, context_instance=RequestContext(request))

def contacted(request):
    return render_to_response('contacted.html', {}, context_instance=RequestContext(request))

def login(request, template_name):
    if request.user.is_authenticated():
        return redirect_to(request, url ='/thegame/userprofile/')
    else:
        return generic_login(request, template_name)

def create_account(request, template_name):
    
    # if user already logged in, no need to be creating accounts
    if request.user.is_authenticated():
        return redirect_to(request, url ='/thegame/userprofile/')
    
    if request.method == 'POST': # If the form has been submitted...
        form = UserCreationForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            world = form.cleaned_data['join_world']
            
            new_user = User(username=form.cleaned_data['username'], 
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'], 
                        last_name=form.cleaned_data['last_name'],)
            new_user.set_password(form.cleaned_data['password1'])
            new_user.is_active = False
            new_user.save()
            
            new_userprofile = UserProfile(user=new_user,)
            new_userprofile.save()
            
            new_membership = Membership(user = new_userprofile, wealth=world.initial_wealth, world = world, approved=False)
            new_membership.save()
            
            # send mail to the world admins, now that someone applied.
            email_list = []
            for master in world.mastered_worlds.all():
                email_list.append(master.user.email)
            send_mail('User application received for world %s' % (world.name,),
                    "This is an automatically generated email. Do not reply to this email. \n\nA user application for world '%(world)s' has been received.\n\nUsername: %(username)s\nFirst name: %(firstname)s\nLast name: %(lastname)s\nEmail: %(email)s\n\nTo activate or reject this account, visit http://financegame.dreamhosters.com/" % \
                    {'world':world.name, 
                        'username':new_user.username, 
                        'firstname': new_user.first_name, 
                        'lastname':new_user.last_name, 
                        'email':new_user.email}, 
                    settings.SERVER_EMAIL, email_list)
            
            return HttpResponseRedirect('/accounts/account_created/')
    else:
        form = UserCreationForm()
        
    return render_to_response(template_name, {'form':form})

def account_created(request, template_name):
    return render_to_response(template_name, {})
    
@login_required
def user_profile(request):
    user_membership_list = request.user.get_profile().membership_set.all()
    mastered_membership_list = user_membership_list.filter(is_master=True)
    world_and_user_list= []
    for membership in mastered_membership_list:
        world_and_user_list.append({'world':membership.world, 'pending_users':membership.world.membership_set.filter(approved = False)})
    
    return render_to_response('userprofile.html', {'user_membership_list':user_membership_list, 'mastered_membership_list':mastered_membership_list, 'world_and_user_list':world_and_user_list}, context_instance=RequestContext(request))

@login_required
def user_profile_edit(request):
    return HttpResponse('Edit user profile here')

@login_required
def world_list(request):
    user_world_list = request.user.get_profile().world_memberships.all()
    return render_to_response('world_list.html', {'user_world_list':user_world_list}, context_instance=RequestContext(request))

@login_required
def world_detail(request, world_id):
    world = get_object_or_404(World, pk=world_id)
    user_membership = world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    return render_to_response('world_detail.html', {'world':world, 'user_membership':user_membership}, context_instance=RequestContext(request))
        
@login_required
def period_detail(request, world_id, period_id):
    period = get_object_or_404(Period, pk=period_id)
    world = get_object_or_404(World, pk=world_id)
    
    user_membership = world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')

    # if our period hasn't started yet, don't show the info.
    if not period.is_started() and not world.user_is_master(request.user):
        request.user.message_set.create(message = "Period " + unicode(period.number) + " of World " + world.name + " has not yet started.")
        return redirect_to(request, url ='/thegame/userprofile/')

    return render_to_response('period_detail.html', {'period':period, 'world':world, 'user_membership':user_membership}, context_instance=RequestContext(request))

@login_required
def period_results(request, world_id, period_id):
    period = get_object_or_404(Period, pk=period_id)
    world = get_object_or_404(World, pk=world_id)
    
    user_membership = world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    # if our period hasn't completed yet, don't show the info.
    if not period.is_ended():
        request.user.message_set.create(message = "Period " + unicode(period.number) + " of World " + world.name + " is not yet complete.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    period_result_list = period.periodsummary_set.all().order_by('-wealth_created')
    return render_to_response('period_results.html', {'period':period, 'world':world, 'user_membership':user_membership, 'period_result_list':period_result_list}, context_instance=RequestContext(request))

@login_required
def bid_history(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id)
    
    user_membership = auction.asset.period.world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    # if our period hasn't started yet, don't show the info.
    if not auction.asset.period.is_started() and not request.user.is_staff:
        request.user.message_set.create(message = "Period " + unicode(auction.asset.period.number) + " of World " + auction.asset.period.world.name + " has not yet started.")
        return redirect_to(request, url ='/thegame/userprofile/')
    else:
        return render_to_response('bid_history.html', {'auction':auction, 'user_membership':user_membership}, context_instance=RequestContext(request))

@login_required
def auction_detail(request, auction_id):
    '''Process a bid request
    
    Logic:
    if auction is ended, say so, don't do anything.
    if form input is bad (non-numeric, or too many decimals, or too low number): say so
    if form input is good:
        create the new bid item
        update the auction model with new price, and new end time (add 2 minutes to end time)
            if no other bids, current price becomes starting bid, 
            if other bids, compare to the current highest bid, and set price to next-lowest-bid + 1
            set endtime to currenttime + interval, if currenttime+interval <= max_end_time and currenttime + interval > endtime, otherwise, set to max_end_time
        check to see who's the highest bid, and set that auction property.
        
    '''
    auction = get_object_or_404(Auction, pk=auction_id)
    
    user_membership = auction.asset.period.world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    # if our period hasn't started yet, don't show the info.
    if not auction.asset.period.is_started() and not request.user.is_staff:
        request.user.message_set.create(message = "Period " + unicode(auction.asset.period.id) + " of World " + auction.asset.period.world.name + " has not yet started.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    # if no form has been submitted, display the auction.
    if not request.POST:
        return render_to_response('auction_detail.html', {'auction':auction, 'user_membership':user_membership}, context_instance=RequestContext(request))
    
    ## test if auction is ended
    if auction.is_ended():
        return render_to_response('auction_detail.html', {'auction':auction, 'user_membership':user_membership, 'error_message':'Auction has ended.'}, context_instance=RequestContext(request))
        
    ## test if auction is started
    if not auction.asset.period.is_started():
        return render_to_response('auction_detail.html', {'auction':auction, 'user_membership':user_membership, 'error_message':'Auction not yet started.'}, context_instance=RequestContext(request))
    
    ## test form input
    try:
        bid_amount = float(request.POST['bid_amount'])
    except KeyError:
        return render_to_response('auction_detail.html', {'auction':auction, 'user_membership':user_membership, 'error_message':'You did not enter a bid.'}, context_instance=RequestContext(request))
    except ValueError:
        return render_to_response('auction_detail.html', {'auction':auction, 'user_membership':user_membership, 'error_message':'Enter a numeric amount of dollars and cents.'}, context_instance=RequestContext(request))

    if bid_amount != round(bid_amount, 2):
        return render_to_response('auction_detail.html', {'auction':auction, 'user_membership':user_membership, 'error_message':'Fractions of a cent are not allowed.'}, context_instance=RequestContext(request))
        
    ## throw up a confirm-bid page
    try: 
        confirmation = request.POST['confirmation']
    except:
        request.user.message_set.create(message = 'Please confirm your bid')
        return render_to_response('bid_confirm.html', {'auction':auction, 'user_membership':user_membership, 'bid_amount':bid_amount}, context_instance=RequestContext(request))
    
    if confirmation != "True":
        return render_to_response('bid_confirm.html', {'auction':auction, 'user_membership':user_membership, 'error_message':'Something went wrong in the processing of your bid submission. Please try again.'}, context_instance=RequestContext(request))
    
    ## now we know input is good. let's update the database.
    ## if user hasn't bid on this item yet, create new bid.
    ## otherwise, update existing amount.
    try:
        new_bid = auction.bid_set.get(bidder__id = request.user.id)
        new_bid.amount = bid_amount
        new_bid.time = datetime.datetime.now()
        new_bid.save()
        bid_message = 'Your bid on this auction has been updated.'
    except ObjectDoesNotExist:
        new_bid = Bid(auction=auction, bidder = request.user, amount = bid_amount, time = datetime.datetime.now())
        new_bid.save()
        bid_message = 'Your bid on this auction has been recorded.'
        
    request.user.message_set.create(message = bid_message)
    return HttpResponseRedirect(auction.get_absolute_url())
    
@login_required
def world_detail_master(request, world_id):
    # world attributes/settings edit form, prefilled
    # list periods, with edit/delete links, create new button
    # list users, with approve/delete/edit links, create new button
    world = get_object_or_404(World, pk=world_id)
    user_membership = world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    if not world.user_is_master(request.user):
        request.user.message_set.create(message = 'You are not authorized to edit this world.')
        return HttpResponseRedirect(world.get_absolute_url())
    
    world_form = WorldForm(instance = world)
    
    # could this ever error if a user is created in the middle, thus creating
    # an unequal number of items in formset and queryset?
    membership_queryset = Membership.objects.filter(world = world).order_by('user__user__username')
    user_formset = MembershipFormSet(queryset = membership_queryset)
    user_formset_dict = dict(zip(membership_queryset, user_formset.forms))
    
        
    return render_to_response('world_detail_master.html', 
            {'world_form':world_form, 
            'user_formset':user_formset, 
            'user_formset_dict': user_formset_dict, 
            'world':world,
            'user_membership':user_membership,}, 
            context_instance=RequestContext(request))

@login_required
def world_detail_master_users(request, world_id):
    '''Process the user changes and redirect to world master.'''
    world = get_object_or_404(World, pk=world_id)
    
    if not world.user_is_member(request.user):
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    if not world.user_is_master(request.user):
        request.user.message_set.create(message = 'You are not authorized to edit this world.')
        return HttpResponseRedirect(world.get_absolute_url())
        
    if request.method == 'POST':
        formset = MembershipFormSet(request.POST, 
                queryset = Membership.objects.filter(world = world).order_by('user__user__username'))
        if formset.is_valid():
            instances = formset.save()
            for membership in instances:
                if membership.approved == True and membership.user.user.is_active == False:
                    user = membership.user.user
                    user.is_active = True
                    user.save()
            
            request.user.message_set.create(message = "Users edited successfully.")
            return HttpResponseRedirect(world.get_absolute_url() + 'master/')
    else:
        return redirect_to(request, url=world.get_absolute_url + 'master/')

@login_required
def world_detail_master_world(request, world_id):
    # world attributes/settings edit form, prefilled
    # list periods, with edit/delete links, create new button
    # list users, with approve/delete/edit links, create new button
    world = get_object_or_404(World, pk=world_id)
    
    if not world.user_is_member(request.user):
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    if not world.user_is_master(request.user):
        request.user.message_set.create(message = 'You are not authorized to edit this world.')
        return HttpResponseRedirect(world.get_absolute_url())
    
    if request.method == 'POST': # If the form has been submitted...
        world_form = WorldForm(request.POST, instance=world) # A form bound to the POST data
        if world_form.is_valid():
            world_form.save()
            
            request.user.message_set.create(message = "World edited successfully.")
            return HttpResponseRedirect(world.get_absolute_url() + 'master/')
    else:
        return redirect_to(request, url=world.get_absolute_url + 'master/')


@login_required
def period_detail_master(request, world_id, period_id):
    # period attributes edit form, prefilled
    # list asset-auctions, with edit/delete links, create new button
    period = get_object_or_404(Period, pk=period_id)
    world = get_object_or_404(World, pk=world_id)
    
    user_membership = world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    if not world.user_is_master(request.user):
        request.user.message_set.create(message = 'You are not authorized to edit this world.')
        return HttpResponseRedirect(period.get_absolute_url())
    
    if request.method == 'POST': # If the form has been submitted...
        period_form = PeriodForm(request.POST, instance=period, queryset = request.user.get_profile().mastered_worlds.all()) # A form bound to the POST data for asset
        if period_form.is_valid():
            new_period = period_form.save()
            
            request.user.message_set.create(message = "Period edited successfully.")
            return HttpResponseRedirect('.')
    else:
        period_form = PeriodForm(instance = period, queryset = request.user.get_profile().mastered_worlds.all())
    
    return render_to_response('period_detail_master.html', {'period':period, 'world':world, 'user_membership':user_membership, 'period_form':period_form}, context_instance=RequestContext(request))

@login_required
def auction_detail_master(request, auction_id):
    # auction edit form, prefilled
    # list bids, with delete links? or do that in bid history
    
    auction = get_object_or_404(Auction, pk=auction_id)
    
    user_membership = auction.asset.period.world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    if not auction.asset.period.world.user_is_master(request.user):
        request.user.message_set.create(message = 'You are not authorized to edit this world.')
        return HttpResponseRedirect(auction.get_absolute_url())
    
    if request.method == 'POST': # If the form has been submitted...
        asset_form = AssetForm(request.POST, instance=auction.asset, queryset = auction.asset.period.world.period_set.all()) # A form bound to the POST data for asset
        auction_form = AuctionForm(request.POST, instance=auction) # A form bound to the POST data for auction
        if asset_form.is_valid() and auction_form.is_valid():
            new_asset = asset_form.save()
            new_auction = auction_form.save()
            
            request.user.message_set.create(message = "Auction edited successfully.")
            return HttpResponseRedirect('.')
        else:
            request.user.message_set.create(message = "Errors in form.")
    else:
        asset_form = AssetForm(instance = auction.asset, queryset = auction.asset.period.world.period_set.all())
        auction_form = AuctionForm(instance = auction)

    return render_to_response('auction_detail_master.html', {'auction':auction, 'user_membership':user_membership, 'asset_form':asset_form, 'auction_form':auction_form}, context_instance=RequestContext(request))

@login_required
def bid_history_master(request, auction_id):
    # list bids, with delete and edit links
    auction = get_object_or_404(Auction, pk=auction_id)
    
    user_membership = auction.asset.period.world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    if auction.asset.period.world.user_is_master(request.user):
        return render_to_response('bid_history_master.html', {'auction':auction, 'user_membership':user_membership}, context_instance=RequestContext(request))
    else:
        request.user.message_set.create(message = 'You are not authorized to edit this world.')
        return HttpResponseRedirect(auction.get_absolute_url())

@login_required
def period_results_master(request, world_id, period_id):
    # button to regenerate period results
    
    period = get_object_or_404(Period, pk=period_id)
    world = get_object_or_404(World, pk=world_id)
    
    user_membership = world.user_is_member(request.user)
    if not user_membership:
        request.user.message_set.create(message = "Access denied. Either you are not a member of the world requested, or your membership has not yet been approved.")
        return redirect_to(request, url ='/thegame/userprofile/')
    
    if not world.user_is_master(request.user):
        request.user.message_set.create(message = 'You are not authorized to edit this world.')
        return HttpResponseRedirect(period.get_absolute_url())
    
    # if our period hasn't completed yet, don't show the info.
    if not period.is_ended():
        request.user.message_set.create(message = "Period " + unicode(period.number) + " of World " + world.name + " is not yet complete.")
        return HttpResponseRedirect(request.user.get_profile().get_absolute_url())
    
    if request.method == 'POST': # If the form has been submitted...
        form = RecalculatePeriodResultsForm(request.POST)
        if form.is_valid():
            #period.recalc_period_summary(form.cleaned_data['update_wealth'])
            period.calc_period_summary(force=True, 
                    recalc_auctions = form.cleaned_data['recalc_auctions'])
            request.user.message_set.create(message = "Results recalculated.")
            return HttpResponseRedirect('.')
        else: 
            request.user.message_set.create(message = "Form errors.")
    else:
        form = RecalculatePeriodResultsForm()
    
    period_result_list = period.periodsummary_set.all().order_by('-wealth_created')
    return render_to_response('period_results_master.html', {'period':period, 'world':world, 'user_membership':user_membership, 'period_result_list':period_result_list, 'form':form}, context_instance=RequestContext(request))
