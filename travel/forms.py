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
class TravelLogForm(forms.Form):
    arrival = DateUtilField(required=False)
    departure = DateUtilField(required=False)
    rating = forms.ChoiceField(choices=TravelLog.RATING_CHOICES, initial='3')
    note = TextField(required=False)
    
    #---------------------------------------------------------------------------
    def __init__(self, instance, data=None, prefix=None):
        super(TravelLogForm, self).__init__(data=data, prefix=prefix)
        self.instance = instance
        
    #---------------------------------------------------------------------------
    def save(self, user):
        arrival = self.cleaned_data['arrival']
        departure = self.cleaned_data['departure']
        if arrival and not departure:
            departure = arrival
            
        if departure and not arrival:
            arrival = departure
            
        entry = TravelLog.objects.create(
            arrival=arrival,
            departure=departure,
            rating=self.cleaned_data['rating'],
            entity=self.instance,
            user=user
        )
        
        note = self.cleaned_data['note']
        if note:
            entry.notes.create(type='B', text=note)
            
        return entry


#===============================================================================
class SupportForm(forms.Form):
    message = TextField(label='Description:')
    
