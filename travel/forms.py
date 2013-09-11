from datetime import datetime, date

from django import forms
from django.conf import settings
from django.forms import fields
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from jargon.forms import TextField
from jargon.utils.dates import parse as dtparse
from jargon.apps.annotation.models import Markup

from travel import models as travel
from travel.utils import WikiFlagUtil

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
    
    #---------------------------------------------------------------------------
    def widget_attrs(self, widget):
        return {'placeholder': 'Search'}
    
    

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
    rating = forms.ChoiceField(choices=travel.TravelLog.RATING_CHOICES, initial='3')
    note = TextField(required=False)

    #===========================================================================
    class Meta:
        model = travel.TravelLog
        fields = ('arrival', 'departure', 'rating', 'note')
    
    #---------------------------------------------------------------------------
    def __init__(self, *args, **kws):
        super(TravelLogForm, self).__init__(*args, **kws)
        instance = kws.get('instance', None)
        if instance and instance.notes:
            self.fields['note'].initial = instance.notes.text
        
    #---------------------------------------------------------------------------
    def save(self, user=None, entity=None):
        data = self.cleaned_data
        entry = super(TravelLogForm, self).save(commit=False)
        if user:
            entry.user = user
            
        if entity:
            entry.entity = entity
            
        entry.save()
        entry.update_notes(data.get('note', ''))
            
        return entry


#===============================================================================
class SupportForm(forms.Form):
    message = TextField(label='Description:')


#===============================================================================
class EntityForm(forms.ModelForm):
    flag_data = forms.CharField(label="New Flag URL", required=False)
    
    #===========================================================================
    class Meta:
        model = travel.Entity
        fields = (
            'name',
            'full_name',
            'lat',
            'lon',
            'locality',
            'flag_data'
        )
        
    #---------------------------------------------------------------------------
    def __init__(self, *args, **kws):
        super(EntityForm, self).__init__(*args, **kws)
        if self.instance.type.abbr not in ('co', 'st'):
            del self.fields['flag_data']
            
    #---------------------------------------------------------------------------
    def clean_flag_data(self):
        url = self.cleaned_data.get('flag_data', None)
        if url:
            try:
                return WikiFlagUtil.create(url, self.instance)
            except ValueError, why:
                raise forms.ValidationError(why)

    #---------------------------------------------------------------------------
    def save(self):
        super(EntityForm, self).save()
        flag_data = self.cleaned_data.get('flag_data')
        if flag_data:
            flag_data.save()
