import re
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
from path import path


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


_flag_url_re =  re.compile(r'(.*)/(\d+)px(.*)')


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
        import requests
        url = self.cleaned_data['flag_data']
        print 'url', url
        # 'http://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Flag_of_Wyoming.svg/120px-Flag_of_Wyoming.svg.png'

        ref         = self.instance.code.lower()
        base_dir    = path(self.instance.flag_dir)
        parent_dir  = base_dir / ref
        static_root = path(settings.STATIC_ROOT)
        flag_path   = travel.BASE_FLAG_DIR / parent_dir / ('%s-%%s.png' % (ref,))

        abs_dir = static_root / travel.BASE_FLAG_DIR / parent_dir
        if not abs_dir.exists():
            abs_dir.makedirs()

        data = {
            'sizes':     {},
            'url':       url,
            'ref':       self.instance.code.lower(),
            'base_dir':  path(self.instance.flag_dir),
            'flag_path': travel.BASE_FLAG_DIR / parent_dir / ('%s-%%s.png' % (ref,)),
        }

        for size in ('16', '32', '64', '128', '256', '512'):
            size_url = _flag_url_re.sub(r'\1/%spx\3' % size, url)
            # print size, size_url
            r = requests.get(size_url)
            if r.status_code != 200:
                raise forms.ValidationError('Status %s (%s)' % (r.status_code, size_url))

            data['sizes'][static_root / (flag_path % size)] = r.content

        return data
        
    #---------------------------------------------------------------------------
    def save(self):
        super(EntityForm, self).save()
        data = self.cleaned_data.get('flag_data')
        if data:
            for fn, bytes in data['sizes'].iteritems():
                with open(fn, 'wb') as fp:
                    fp.write(bytes)

            flag_path      = data['flag_path']
            flag           = self.instance.flag or travel.Flag()
            flag.source    = data['url']
            flag.base_dir  = data['base_dir']
            flag.ref       = data['ref']
            flag.width_16  = flag_path %  16
            flag.width_32  = flag_path %  32
            flag.width_64  = flag_path %  64
            flag.width_128 = flag_path % 128
            flag.width_256 = flag_path % 256
            flag.width_512 = flag_path % 512

            flag.save()
            if not self.instance.flag:
                self.instance.flag = flag
                self.instance.save()
        