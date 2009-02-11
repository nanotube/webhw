from django import forms
from django.db import models
from django.conf import settings
from django.contrib.admin import widgets as admin_widgets
from django.contrib.auth.models import User
from financegame.thegame.models import World, Asset, Auction, Period
import re

class UserCreationForm(forms.Form):
    username = forms.CharField(max_length=30)
    description = forms.CharField(max_length=200, label="Names of team members")
    email = forms.EmailField(max_length=75)
    password1 = forms.CharField(max_length=30, label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=30, label="Password (again)", widget=forms.PasswordInput)
    join_world = forms.ModelChoiceField(queryset=World.objects.all())
    
    def clean_username(self):
        data = self.cleaned_data['username']
        try:
            User.objects.get(username=data)
            raise forms.ValidationError("This username is already taken. Please choose another.")
            
        except User.DoesNotExist:
            if re.search(r'^[a-zA-Z0-9_]+$', data):
                return data
            else:
                raise forms.ValidationError("Username can only contain alphanumeric characters (letters, digits and underscores). Please choose another username.")
        
        # Always return the cleaned data, whether you have changed it or
        # not.
        return data
        
    def clean_join_world(self):
        data = self.cleaned_data['join_world']
        
        try:
            World.objects.get(id = data.id)
            return data
        except World.DoesNotExist:
            raise forms.ValidationError("The world you have chosen does not exist. Choose another world.")
        
        # Always return the cleaned data, whether you have changed it or
        # not.
        return data
        
    def clean(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                del self.cleaned_data['password1']
                del self.cleaned_data['password2']
                raise forms.ValidationError("Your two password entries did not match. Please re-enter your passwords.")
        
        return self.cleaned_data
        
class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)

class WorldForm(forms.ModelForm):
    class Meta:
        model = World
        exclude = ('mastered_worlds',)
        
class AuctionForm(forms.ModelForm):
    end_time = forms.DateTimeField(widget=admin_widgets.AdminSplitDateTime())
    class Meta:
        model = Auction
        exclude = ('asset','high_bid','current_price','max_end_time',)
    
    class Media:
        css = { 'all': ('/site_media/css/calendar.css',) }
        #js = (settings.ADMIN_MEDIA_PREFIX + "js/core.js", )

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        exclude = ('period',)

class PeriodForm(forms.ModelForm):
    start_time = forms.DateTimeField(widget=admin_widgets.AdminSplitDateTime())
    end_time = forms.DateTimeField(widget=admin_widgets.AdminSplitDateTime())
    class Meta:
        model = Period

