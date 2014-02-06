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
from travel import utils as travel_utils


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

    search = SearchField(label='Search', required=False)
    type = forms.ChoiceField(choices=TYPE_OPTIONS, required=False)


#===============================================================================
class WidgetAttrsMixin(object):
    
    #---------------------------------------------------------------------------
    def widget_attrs(self, widget):
        attrs = super(WidgetAttrsMixin, self).widget_attrs(widget)
        attrs.update({'class' : 'form-control input-sm'})
        return attrs


#===============================================================================
class TravelDateUtilField(WidgetAttrsMixin, DateUtilField): pass
class TravelRating(WidgetAttrsMixin, forms.ChoiceField): pass
class TravelNote(WidgetAttrsMixin, TextField): pass

#===============================================================================
class TravelLogForm(forms.ModelForm):
    arrival = TravelDateUtilField(required=False)
    rating = TravelRating(choices=travel.TravelLog.RATING_CHOICES, initial='3')
    note = TravelNote(required=False)

    #===========================================================================
    class Meta:
        model = travel.TravelLog
        fields = ('arrival', 'rating', 'note')
    
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
class LatLonField(forms.CharField):
    
    #---------------------------------------------------------------------------
    def clean(self, value):
        value = super(LatLonField, self).clean(value)
        if value:
            try:
                return travel_utils.parse_latlon(value)
            except ValueError:
                raise forms.ValidationError('Unable to parse lat/lon')


#===============================================================================
class FlagField(forms.CharField):
    
    #---------------------------------------------------------------------------
    def clean(self, value):
        url = super(FlagField, self).clean(value)
        if url:
            try:
                return url, travel.Flag.objects.get_wiki_flags_by_size(url)
            except ValueError, why:
                raise forms.ValidationError(why)


#-------------------------------------------------------------------------------
def _save_flag(instance, flag_data):
    if flag_data:
        instance.update_flags(*flag_data)


#===============================================================================
class EditEntityForm(forms.ModelForm):
    flag_data = FlagField(label='Flag URL', required=False)
    country = forms.ModelChoiceField(queryset=travel.Entity.objects.countries())

    #===========================================================================
    class Meta:
        model = travel.Entity
        fields = (
            'country',
            'name',
            'full_name',
            'code',
            'lat',
            'lon',
            'locality',
            'flag_data'
        )

    #---------------------------------------------------------------------------
    def save(self):
        instance = super(EditEntityForm, self).save()
        _save_flag(instance, self.fields.get('flag_data'))
        return instance


#-------------------------------------------------------------------------------
def entity_meta_fields(*args):
    return ('name', 'full_name') + args  + ('lat_lon', 'flag_data')


#===============================================================================
class _NewEntityForm(forms.ModelForm):
    lat_lon = LatLonField(label='Lat/Lon', required=False)
    flag_data = FlagField(label='Flag URL', required=False)
    
    #===========================================================================
    class Meta:
        model = travel.Entity
        fields = entity_meta_fields()
    
    #---------------------------------------------------------------------------
    def save(self, entity_type):
        instance = super(_NewEntityForm, self).save(commit=False)
        instance.type = entity_type
        
        lat_lon = self.cleaned_data.get('lat_lon')
        if lat_lon:
            self.lat, self.lon = lat_lon
            
        instance.save()
        _save_flag(instance, self.cleaned_data.get('flag_data'))
        return instance


#===============================================================================
class NewCountryForm(_NewEntityForm):
    continent = forms.ModelChoiceField(queryset=travel.Entity.objects.filter(type__abbr='cn'))

    #===========================================================================
    class Meta(_NewEntityForm.Meta):
        fields = entity_meta_fields('code', 'continent')
    
# country = forms.ModelChoiceField(queryset=travel.Entity.objects.countries())
