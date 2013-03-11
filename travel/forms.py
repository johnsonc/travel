from datetime import datetime, date

from django import forms
from django.conf import settings
from django.forms import fields
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from jargon.forms import TextField, DateUtilField
from travel.models import TravelLog


#===============================================================================
class SearchInput(forms.TextInput):
    input_type = 'search'


#===============================================================================
class SearchField(forms.CharField):
    widget = SearchInput
    

#===============================================================================
class SearchForm(forms.Form):
    TYPE_OPTIONS = (
        ('',   'All Locales'),
        ('co', 'Country'),
        ('st', 'State'),
        ('ap', 'Airport'),
        ('ct', 'City'),
        ('np', 'National Park'),
        ('lm', 'Landmark'),
        ('cn', 'Continent'),
        ('wh', 'World Heritage Site'),
    )

    travel_search = SearchField(label='Search')
    type = forms.ChoiceField(choices=TYPE_OPTIONS, required=False)


#===============================================================================
class TravelLogForm(forms.ModelForm):
    arrival = DateUtilField(required=False)
    departure = DateUtilField(required=False)
    rating = forms.ChoiceField(choices=TravelLog.RATING_CHOICES, initial='3')
    note = TextField(required=False)

    #===========================================================================
    class Meta:
        model = TravelLog
        fields = ('arrival', 'departure', 'rating', 'note')
        
    #---------------------------------------------------------------------------
    def save(self, user=None, entity=None):
        data = self.cleaned_data
        if data['arrival'] and not data['departure']:
            data['departure'] = data['arrival']
            
        if data['departure'] and not data['arrival']:
            data['arrival'] = data['departure']
            
        entry = super(TravelLogForm, self).save(commit=False)
        if user:
            entry.user = user
            
        if entity:
            entry.entity = entity
            
        entry.save()
        note = self.cleaned_data['note']
        if note:
            entry.notes.create(type='B', text=note)
            
        return entry


#===============================================================================
class SupportForm(forms.Form):
    message = TextField(label='Description:')
    
