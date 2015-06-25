import re
import os
import operator
from collections import Counter

from django.conf import settings
from django.db import models
from django.db.models import Count, Min, Max, Q
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.functional import cached_property

import pytz
from choice_enum import ChoiceEnumeration
import travel.utils as travel_utils
from .managers import *

GOOGLE_MAPS             = 'http://maps.google.com/maps?q={}'
GOOGLE_MAPS_LATLON      = 'http://maps.google.com/maps?q={},+{}&iwloc=A&z=10'
GOOGLE_SEARCH_URL       = 'http://www.google.com/search?as_q={}'
WIKIPEDIA_URL           = 'http://en.wikipedia.org/wiki/Special:Search?search={}&go=Go'
WORLD_HERITAGE_URL      = 'http://whc.unesco.org/en/list/{}'
BASE_FLAG_DIR           = 'img/flags'
STAR                    = mark_safe('&#9733;')
WORLD_HERITAGE_CATEGORY = { 'C': 'Cultural', 'N': 'Natural', 'M': 'Mixed' }


#-------------------------------------------------------------------------------
def flag_upload(size):
    def upload_func(instance, filename):
        name = '{}-{}{}'.format(instance.ref, size, os.path.splitext(filename)[1])
        return  '{}/{}/{}'.format(BASE_FLAG_DIR, instance.base_dir, name)
    return upload_func


#-------------------------------------------------------------------------------
def svg_upload(instance, filename):
    return  '{}/{}/flag.svg'.format(BASE_FLAG_DIR, instance.base_dir)


#===============================================================================
class TravelFlag(models.Model):
    source = models.CharField(max_length=255)
    base_dir = models.CharField(max_length=8)
    ref = models.CharField(max_length=6)
    thumb  = models.ImageField(upload_to=flag_upload(32), blank=True)
    large = models.ImageField(upload_to=flag_upload(128), blank=True)
    svg = models.FileField(upload_to=svg_upload, blank=True)
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'travel_flag'
    
    #---------------------------------------------------------------------------
    @property
    def image_url(self):
        if self.svg:
            if os.path.exists(self.svg.path):
                return self.svg.url
        return self.large.url
    
    #---------------------------------------------------------------------------
    def update(self, url, base, ref, svg, thumb, large):
        join        = os.path.join
        ref         = ref.lower()
        media_root  = settings.MEDIA_ROOT
        parent_dir  = join(BASE_FLAG_DIR, base, ref)
        abs_dir     = join(media_root, parent_dir)
        path_fmt    = join(parent_dir, '%s-%%s.png' % (ref,))

        if not os.path.exists(abs_dir):
            os.makedirs(abs_dir)
        
        self.source   = url
        self.base_dir = base
        self.ref      = ref
        self.svg      = None
        
        for attr, data, size in (('thumb', thumb, 32), ('large', large, 128)):
            if data:
                flag_path = path_fmt % size
                setattr(self, attr, flag_path)
                with open(join(media_root, flag_path), 'wb') as fp:
                    fp.write(data)
            else:
                setattr(self, attr, None)
        
        if svg:
            self.svg = join(parent_dir, 'flag.svg')
            with open(join(media_root, parent_dir, 'flag.svg'), 'wb') as fp:
                fp.write(svg)
        
        self.save()


#===============================================================================
class TravelBucketList(models.Model):
    owner = models.ForeignKey(User)
    title = models.CharField(max_length=100)
    is_public = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    subscribers = models.ManyToManyField(User, related_name='todo_subscriber_set')
    entities = models.ManyToManyField('TravelEntity', related_name='todo_list_set')
    last_update = models.DateTimeField(auto_now=True)
    
    objects = TravelBucketListManager()

    #===========================================================================
    class Meta:
        db_table = 'travel_todo_list'

    #---------------------------------------------------------------------------
    def get_absolute_url(self):
        return reverse('travel-bucket', args=[self.id])

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return self.title

    #---------------------------------------------------------------------------
    def user_results(self, user):
        all_entities = self.entities.select_related()
        if not user.is_authenticated():
            return 0, [(e, 0) for e in all_entities]

        logged_entities = Counter(TravelLog.objects.filter(
            user=user,
            entity__in=all_entities
        ).values_list('entity__id', flat=True))

        entities = [
            (entity, logged_entities.get(entity.id, 0))
            for entity in all_entities
        ]
        done = sum([1 if b else 0 for a,b in entities])
        return done, entities


#===============================================================================
class TravelProfile(models.Model):
    
    #===========================================================================
    class Access(ChoiceEnumeration):
        PUBLIC    = ChoiceEnumeration.Option('PUB',  'Public')
        PRIVATE   = ChoiceEnumeration.Option('PRI',  'Private')
        PROTECTED = ChoiceEnumeration.Option('PRO',  'Protected', default=True)
    
    user   = models.OneToOneField(User, related_name='travel_profile')
    access = models.CharField(max_length=3, choices=Access.CHOICES, default=Access.DEFAULT)
    
    objects = TravelProfileManager()
    
    class Meta:
        db_table = 'travel_profile'
    
    #---------------------------------------------------------------------------
    def public_url(self):
        return reverse('travel-profile', args=[self.user.username])

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return unicode(self.user)
        
    #---------------------------------------------------------------------------
    def history_json(self):
        return TravelLog.history_json(self.user)
    
    #---------------------------------------------------------------------------
    is_public    = property(lambda self: self.access == self.Access.PUBLIC)
    is_private   = property(lambda self: self.access == self.Access.PRIVATE)
    is_protected = property(lambda self: self.access == self.Access.PROTECTED)


#-------------------------------------------------------------------------------
def profile_factory(sender, instance, created=False, **kws):
    if created:
        TravelProfile.objects.get_or_create(user=instance)


models.signals.post_save.connect(profile_factory, sender=User)


#===============================================================================
class TravelEntityType(models.Model):
    abbr  = models.CharField(max_length=4, db_index=True)
    title = models.CharField(max_length=25)
    
    class Meta:
        db_table = 'travel_entitytype'

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return self.title


#-------------------------------------------------------------------------------
def wikipedia_url(entity):
    return WIKIPEDIA_URL.format(travel_utils.nice_url(entity.full_name))


#-------------------------------------------------------------------------------
def world_heritage_url(entity):
    return WORLD_HERITAGE_URL.format(entity.code)


_default_external_handler = ('Wikipedia', wikipedia_url)
_external_url_handlers = {
    'wh': ('UNESCO', world_heritage_url)
}


#===============================================================================
class TravelEntity(models.Model):
    
    #===========================================================================
    class Subnational(ChoiceEnumeration):
        STATE                = ChoiceEnumeration.Option('S', 'State', default=True)
        PROVINCE             = ChoiceEnumeration.Option('P', 'Province')
        DISTRICT             = ChoiceEnumeration.Option('D', 'District')
        TERRITORY            = ChoiceEnumeration.Option('T', 'Territory')
        COMMONWEALTH         = ChoiceEnumeration.Option('W', 'Commonwealth')
        COUNTY               = ChoiceEnumeration.Option('C', 'County')
        REGION               = ChoiceEnumeration.Option('R', 'Region')
        AUTONOMOUS_COMMUNITY = ChoiceEnumeration.Option('A', 'Autonomous Community')

    geonameid = models.IntegerField(default=0)
    type      = models.ForeignKey(TravelEntityType, related_name='entity_set')
    code      = models.CharField(max_length=6, db_index=True)
    name      = models.CharField(max_length=175)
    full_name = models.CharField(max_length=175)
    lat       = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    lon       = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    category  = models.CharField(blank=True, max_length=4)
    locality  = models.CharField(max_length=256, blank=True)

    flag      = models.ForeignKey(TravelFlag, null=True, blank=True,on_delete=models.SET_NULL)
    capital   = models.ForeignKey('self', related_name='capital_set',   blank=True, null=True)
    state     = models.ForeignKey('self', related_name='state_set',     blank=True, null=True)
    country   = models.ForeignKey('self', related_name='country_set',   blank=True, null=True)
    continent = models.ForeignKey('self', related_name='continent_set', blank=True, null=True)
    tz        = models.CharField('timezone', max_length=40, blank=True)
    #extras    = models.TextField(blank=True)

    objects   = TravelEntityManager()
    
    #===========================================================================
    class Meta:
        ordering = ('name',)
        db_table = 'travel_entity'
    
    #===========================================================================
    class Related:
        ENTITY_TYPES = {'co': 'entity_set__country', 'st': 'entity_set__state'}
        DETAILS = {
            'co': 'Countries',
            'st': 'States, provinces, territories, etc',
            'ct': 'Cities',
            'ap': 'Airports',
            'np': 'National Parks',
            'lm': 'Landmarks',
            'wh': 'World Heriage Sites',
        }
        BY_TYPE_PARAMS = {
            'co': 'country',
            'st': 'state',
            'cn': {
                'co': 'continent',
                'default': 'country__continent'
            }
        }
    
    #---------------------------------------------------------------------------
    def __unicode__(self):
        return self.name
    
    #---------------------------------------------------------------------------
    def descriptive_name(self):
        abbr = self.type.abbr
        if abbr in ('co', 'cn'):
            pass
        elif abbr == 'ct':
            what = self.state or self.country
            what = ', {}'.format(what) if what else ''
            return '{}{}'.format(self, what)
        return unicode(self)
    
    #---------------------------------------------------------------------------
    @cached_property
    def code_url_bit(self):
        code = self.code or self.id
        if self.type.abbr in ('st', 'wh'):
            code = '{}-{}'.format(self.country.code, code) if self.country else code
        return code
        
    #---------------------------------------------------------------------------
    def _permalink_args(self):
        code = self.code or self.id
        if self.type.abbr in ('st', 'wh'):
            code = '{}-{}'.format(self.country.code, code) if self.country else code
        
        return [self.type.abbr, self.code_url_bit]
        
    #---------------------------------------------------------------------------
    def get_absolute_url(self):
        return reverse('travel-entity', args=self._permalink_args())

    #---------------------------------------------------------------------------
    def get_edit_url(self):
        return reverse('travel-entity-edit', args=self._permalink_args())
    
    #---------------------------------------------------------------------------
    def wikipedia_search_url(self):
        return WIKIPEDIA_URL % travel_utils.nice_url(entity.full_name)
        
    #---------------------------------------------------------------------------
    def _external_handler(self):
        return _external_url_handlers.get(self.type.abbr, _default_external_handler)
        
    #---------------------------------------------------------------------------
    def external_url(self):
        handler = self._external_handler()[1]
        return handler(self)

    #---------------------------------------------------------------------------
    def external_url_name(self):
        return self._external_handler()[0]

    #---------------------------------------------------------------------------
    def category_detail(self):
        if self.type.abbr == 'wh':
            return WORLD_HERITAGE_CATEGORY.get(self.category, 'Unknown')
            
        return self.category
    
    #---------------------------------------------------------------------------
    @cached_property
    def timezone(self):
        return (
               self.tz
            or (self.state and self.state.timezone)
            or (self.country and self.country.timezone)
            or 'UTC'
        )
    
    #---------------------------------------------------------------------------
    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)
    
    #---------------------------------------------------------------------------
    def get_continent(self):
        if self.continent:
            return self.continent
        elif self.country:
            return self.country.continent

    #---------------------------------------------------------------------------
    @property
    def type_detail(self):
        if self.type.abbr == 'st':
            return TravelEntity.Subnational.CHOICES_DICT.get(self.category, self.type.title)
            
        return self.type.title
    
    #---------------------------------------------------------------------------
    @property
    def relationships(self):
        abbr = self.type.abbr
        qs = None
        if abbr == 'cn':
            qs = TravelEntityType.objects.distinct().filter(
                Q(entity_set__continent=self) | Q(entity_set__country__continent=self)
            )
        else:
            key = self.Related.ENTITY_TYPES.get(abbr)
            qs = TravelEntityType.objects.distinct().filter(**{key: self})

        return qs.annotate(cnt=Count('abbr')).values_list('abbr', 'cnt') if qs else ()

    #---------------------------------------------------------------------------
    @property
    def related_entities(self):
        return [
            {'abbr': abbr, 'text': self.Related.DETAILS[abbr], 'count': cnt}
            for abbr, cnt in self.relationships
        ]
        
    #---------------------------------------------------------------------------
    @property
    def flag_dir(self):
        abbr = self.type.abbr
        if abbr == 'co' or abbr == 'ct':
            return abbr
        elif abbr == 'st' and self.country:
            return 'st/{}'.format(self.country.code.lower())
        return ''
    
    #---------------------------------------------------------------------------
    def related_by_type(self, type):
        key = self.Related.BY_TYPE_PARAMS[self.type.abbr]
        if isinstance(key, dict):
            key = key.get(type.abbr, key['default'])
        return TravelEntity.objects.filter(**{key: self, 'type': type})
        
    #---------------------------------------------------------------------------
    def update_flag(self, flag_url):
        flag = self.flag if self.flag and not self.flag.is_locked else TravelFlag()
        svg, thumb, large = travel_utils.get_flag_data(flag_url)
        flag.update(flag_url, self.flag_dir, self.code, svg, thumb, large)
        self.flag = flag
        self.save()
        return flag

    #---------------------------------------------------------------------------
    @property
    def lower(self):
        return self.code.lower()
        
    #---------------------------------------------------------------------------
    @property
    def google_maps_url(self):
        if self.lat or self.lon:
            return GOOGLE_MAPS_LATLON.format(self.lat, self.lon)
        else:
            return GOOGLE_MAPS.format(travel_utils.nice_url(self.name),)


#===============================================================================
class TravelLog(models.Model):
    
    RATING_CHOICES = (
        (1, mark_safe(STAR * 5)),
        (2, mark_safe(STAR * 4)),
        (3, mark_safe(STAR * 3)),
        (4, mark_safe(STAR * 2)),
        (5, mark_safe(STAR * 1)),
    )
    
    arrival = models.DateTimeField()
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=3)
    user = models.ForeignKey(User, related_name='travellog_set')
    notes = models.TextField(blank=True)
    entity = models.ForeignKey(TravelEntity)
    
    objects = TravelLogManager()
    
    #===========================================================================
    class Meta:
        get_latest_by = 'arrival'
        ordering = ('-arrival',)

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return u'{} | {}'.format(self.entity, self.user)

    #---------------------------------------------------------------------------
    @property
    def local_arrival(self):
        return self.arrival.astimezone(self.entity.tzinfo)
        
    #---------------------------------------------------------------------------
    def get_absolute_url(self):
        return reverse('travel-log-entry', args=[self.user.username, self.id])
    
    #---------------------------------------------------------------------------
    def save(self, *args, **kws):
        if not self.arrival:
            self.arrival = timezone.now()
            
        return super(TravelLog, self).save(*args, **kws)
    
    #---------------------------------------------------------------------------
    def update_notes(self, note):
        self.notes = note
        self.save()

    #---------------------------------------------------------------------------
    @classmethod
    def user_history(cls, user):
        return TravelEntity.objects.filter(travellog__user=user).distinct().annotate(
            num_visits=Count('travellog__user'),
            first_visit=Min('travellog__arrival'),
            recent_visit=Max('travellog__arrival'),
            rating=Min('travellog__rating')
        ).order_by('-recent_visit').values(
            'id', 'code', 'name', 'locality', 'country__name', 'country__code',
            'country__flag__thumb', 'rating', 'recent_visit', 'first_visit',
            'num_visits', 'type__abbr', 'type__title', 'flag__thumb',
        )

    #---------------------------------------------------------------------------
    @classmethod
    def history_json(cls, user):
        return travel_utils.json_dumps(list(cls.user_history(user)))


#===============================================================================
class TravelLanguage(models.Model):
    iso639_1 = models.CharField(blank=True, max_length=2)
    iso639_3 = models.CharField(blank=True, max_length=3)
    name     = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name


#===============================================================================
class TravelCurrency(models.Model):
    iso = models.CharField(max_length=4, primary_key=True)
    name = models.CharField(max_length=50)
    fraction = models.CharField(blank=True, max_length=8)
    fraction_name = models.CharField(blank=True, max_length=15)
    sign = models.CharField(blank=True, max_length=4)
    alt_sign = models.CharField(blank=True, max_length=4)

    class Meta:
        db_table = 'travel_currency'
    
    #---------------------------------------------------------------------------
    def __unicode__(self):
        return self.name


#===============================================================================
class EntityImage(object):
    
    #---------------------------------------------------------------------------
    def __init__(self, entity, location):
        fn = entity.code.lower() + '.gif'
        self.fqdn = os.path.join(settings.MEDIA_ROOT, 'img', location, fn)
        self.exists = os.path.exists(self.fqdn)
        self.url = settings.MEDIA_URL + '/'.join(['img', location, fn])


#===============================================================================
class TravelEntityInfo(models.Model):
    entity = models.OneToOneField(TravelEntity, related_name='entityinfo')
    iso3 = models.CharField(blank=True, max_length=3)
    currency = models.ForeignKey(TravelCurrency, blank=True, null=True)
    denom = models.CharField(blank=True, max_length=40)
    denoms = models.CharField(blank=True, max_length=60)
    language_codes = models.CharField(blank=True, max_length=100)
    phone = models.CharField(blank=True, max_length=20)
    electrical = models.CharField(blank=True, max_length=40)
    postal_code = models.CharField(blank=True, max_length=60)
    tld = models.CharField(blank=True, max_length=8)
    population = models.IntegerField(blank=True, null=True, default=None)
    area = models.IntegerField(blank=True, null=True, default=None)
    languages = models.ManyToManyField(TravelLanguage, blank=True)
    neighbors = models.ManyToManyField(TravelEntity, blank=True)
    
    #===========================================================================
    class Meta:
        db_table = 'travel_entityinfo'
    
    #---------------------------------------------------------------------------
    def __unicode__(self):
        return '<{}: {}>'.format('TravelEntityInfo', self.entity.name)
    
    #---------------------------------------------------------------------------
    @cached_property
    def get_languages(self):
        lang = u', '.join([l.name for l in self.languages.all()])
        if self.language_codes:
            lang = u'{} ({})'.format(lang, self.language_codes)
            
        return lang or 'Unknown'
        
    #---------------------------------------------------------------------------
    @cached_property
    def electrical_info(self):
        if self.electrical:
            v,h,p = self.electrical.split('/')
            return {'volts': v, 'hertz': h, 'plugs': p.split(',')}
        return {}
    
    #---------------------------------------------------------------------------
    @cached_property
    def images(self):
        images = [self.map, self.locator]
        return [i for i in images if i.exists]

    #---------------------------------------------------------------------------
    @cached_property
    def locator(self):
        return EntityImage(self.entity, 'locator')
    
    #---------------------------------------------------------------------------
    @cached_property
    def map(self):
        return EntityImage(self.entity, 'map')
