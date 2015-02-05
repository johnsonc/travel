from datetime import datetime, date
from django import forms
from django.conf import settings
from travel import models as travel
from travel import utils as travel_utils


#===============================================================================
class TextField(forms.CharField):
    widget = forms.Textarea


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
        if value in forms.fields.EMPTY_VALUES:
            return None
        elif isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return datetime(value.year, value.month, value.day)

        try:
            return travel_utils.dt_parse(value)
        except:
            raise forms.ValidationError(self.error_messages['invalid'])


#===============================================================================
class SearchField(forms.CharField):
    
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
class TravelLogForm(forms.ModelForm):
    arrival = DateUtilField(required=False)
    rating = forms.ChoiceField(choices=travel.TravelLog.RATING_CHOICES, initial='3')
    note = TextField(required=False)

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
        if url and url != self.initial:
            try:
                return url, travel.Flag.objects.get_flag_data_by_sizes(url)
            except ValueError, why:
                raise forms.ValidationError(why)


#-------------------------------------------------------------------------------
def _save_flag(instance, flag_data):
    if flag_data:
        instance.update_flags(*flag_data)


#===============================================================================
class EditEntityForm(forms.ModelForm):
    flag_url = FlagField(label='Flag URL', required=False)
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
            'tz',
            'flag_url',
        )
    #---------------------------------------------------------------------------
    def __init__(self, *args, **kws):
        super(EditEntityForm, self).__init__(*args, **kws)
        instance = kws.get('instance', None)
        if instance:
            if instance.type:
                if instance.type.abbr in ('co', 'cn'):
                    del self.fields['country']
            if instance.flag and instance.flag.source:
                self.fields['flag_url'].initial = instance.flag.source
        
    #---------------------------------------------------------------------------
    def save(self):
        instance = super(EditEntityForm, self).save()
        _save_flag(instance, self.cleaned_data.get('flag_url'))
        return instance


#-------------------------------------------------------------------------------
def entity_meta_fields(*args):
    return args + ('name', 'full_name', 'code', 'lat_lon', 'tz', 'flag_data')


#===============================================================================
class _NewEntityForm(forms.ModelForm):
    lat_lon = LatLonField(label='Lat/Lon', required=False)
    flag_data = FlagField(label='Flag URL', required=False)
    
    #===========================================================================
    class Meta:
        model = travel.Entity
        fields = entity_meta_fields()
    
    #---------------------------------------------------------------------------
    def __init__(self, *args, **kws):
        super(_NewEntityForm, self).__init__(*args, **kws)
        self.fields['full_name'].required = False
        self.fields['tz'].required = False
    
    #---------------------------------------------------------------------------
    def save(self, entity_type, **extra_fields):
        instance = super(_NewEntityForm, self).save(commit=False)
        instance.type = entity_type
        instance.full_name = instance.full_name or instance.name
        
        lat_lon = self.cleaned_data.get('lat_lon')
        if lat_lon:
            instance.lat, instance.lon = lat_lon
            
        for key, value in extra_fields.items():
            setattr(instance, key, value)
            
        instance.save()
        _save_flag(instance, self.cleaned_data.get('flag_data'))
        return instance


#===============================================================================
class NewCountryForm(_NewEntityForm):
    continent = forms.ModelChoiceField(queryset=travel.Entity.objects.filter(type__abbr='cn'))

    #===========================================================================
    class Meta(_NewEntityForm.Meta):
        fields = entity_meta_fields('continent')


#===============================================================================
class NewStateForm(_NewEntityForm):

    #===========================================================================
    class Meta(_NewEntityForm.Meta):
        fields = entity_meta_fields()
    
# country = forms.ModelChoiceField(queryset=travel.Entity.objects.countries())
