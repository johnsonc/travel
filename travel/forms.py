from datetime import datetime, date

from django import forms
from django.conf import settings
from django.forms import fields
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from jargon.forms import TextField
from jargon.utils.dates import parse as dtparse
from jargon.apps.annotation.models import Annotation

from travel.models import TravelLog


#===============================================================================
class DateUtilField(forms.Field):
    default_error_messages = {
        'invalid': u'Enter a valid date/time. Try using YYYY/MM/DD HH:MM:SS',
    }

    #---------------------------------------------------------------------------
    def clean(self, value):
        """
        Validates that the input can be converted to a datetime. Returns a
        Python datetime.datetime object.
        """
        super(DateUtilField, self).clean(value)
        if value in fields.EMPTY_VALUES:
            return None
        elif isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return datetime(value.year, value.month, value.day)

        try:
            return dtparse(value)
        except:
            raise forms.ValidationError(self.error_messages['invalid'])


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

    travel_search = SearchField(label='Search', required=False)
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
        entry = super(TravelLogForm, self).save(commit=False)
        if user:
            entry.user = user
            
        if entity:
            entry.entity = entity
            
        entry.save()
        note = data['note']
        if note:
            entry.notes.create(format=Annotation.Format.BASIC, text=note)
            
        return entry


#===============================================================================
class SupportForm(forms.Form):
    message = TextField(label='Description:')
    
