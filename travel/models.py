import re
from datetime import datetime

from django.conf import settings
from django.db import models, connection
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from path import path
from choice_enum import ChoiceEnumeration
import travel.utils as travel_utils


GOOGLE_MAPS             = 'http://maps.google.com/maps?q=%s'
GOOGLE_MAPS_LATLON      = 'http://maps.google.com/maps?q=%s,+%s&iwloc=A&z=10'
GOOGLE_SEARCH_URL       = 'http://www.google.com/search?as_q=%s'
WIKIPEDIA_URL           = 'http://en.wikipedia.org/wiki/Special:Search?search=%s&go=Go'
WORLD_HERITAGE_URL      = 'http://whc.unesco.org/en/list/%s'
BASE_FLAG_DIR           = path('img/flags')
STAR                    = mark_safe('&#9733;')
WORLD_HERITAGE_CATEGORY = { 'C': 'Cultural', 'N': 'Natural', 'M': 'Mixed' }
EXTRA_INFO              = { 'ap': 'IATA'}

#-------------------------------------------------------------------------------
def flag_upload(size):
    def upload_func(instance, filename):
        name = '{}-{}{}'.format(instance.ref, size, path(filename).ext)
        return  '{}/{}/{}'.format(BASE_FLAG_DIR, instance.base_dir, name)
    return upload_func


#===============================================================================
class FlagManager(models.Manager):
    
    #---------------------------------------------------------------------------
    def get_flag_data_by_sizes(self, url, sizes=None):
        if url.endswith('.svg.png'):
            return travel_utils.get_wiki_flags_by_size(url, sizes)
        else:
            return travel_utils.get_flags_from_image_by_size(url, sizes)


#===============================================================================
class Flag(models.Model):
    source = models.CharField(max_length=255)
    base_dir = models.CharField(max_length=8)
    ref = models.CharField(max_length=6)
    width_16  = models.ImageField(upload_to=flag_upload(16), null=True)
    width_32  = models.ImageField(upload_to=flag_upload(32), null=True)
    width_64  = models.ImageField(upload_to=flag_upload(64), null=True)
    width_128 = models.ImageField(upload_to=flag_upload(128), null=True)
    width_256 = models.ImageField(upload_to=flag_upload(256), null=True)
    width_512 = models.ImageField(upload_to=flag_upload(512), null=True)

    objects = FlagManager()
    
    #---------------------------------------------------------------------------
    @property
    def is_locked(self):
        #TODO **hack** - fixme!
        return False if (self.base_dir or self.ref) else True
    
    #---------------------------------------------------------------------------
    def set_flags(self, url, base, ref, sizes):
        base_dir    = path(base)
        ref         = ref.lower()
        static_root = path(settings.STATIC_ROOT)
        parent_dir  = path(BASE_FLAG_DIR) / base_dir / ref
        abs_dir     = static_root / parent_dir
        path_fmt    = parent_dir / ('%s-%%s.png' % (ref,))

        if not abs_dir.exists():
            abs_dir.makedirs()
        
        self.source   = url
        self.base_dir = base_dir
        self.ref      = ref
        for size, bytes in sizes.iteritems():
            flag_path = path_fmt % size
            setattr(self, 'width_%s' % size, flag_path)
            with open(static_root / flag_path, 'wb') as fp:
                fp.write(bytes)

        self.save()


#===============================================================================
class ToDoListManager(models.Manager):
    
    #---------------------------------------------------------------------------
    def all_for_user(self, user):
        return self.filter(models.Q(is_public=True) | models.Q(owner=user))
        
    #---------------------------------------------------------------------------
    def new_list(self, owner, title, entries, is_public=True, description=''):
        tdl = self.create(
            owner=owner, 
            title=title, 
            is_public=is_public, 
            description=description
        )
        
        for e in entries:
            e.todos.create(todo=tdl)
            
        return tdl


#===============================================================================
class ToDoList(models.Model):
    owner = models.ForeignKey(User)
    title = models.CharField(max_length=100)
    is_public = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    subscribers = models.ManyToManyField(User, related_name='todo_subscriber_set')
    entities = models.ManyToManyField('Entity', related_name='todo_list_set')
    last_update = models.DateTimeField(auto_now=True)
    
    objects = ToDoListManager()

    #===========================================================================
    class Meta:
        db_table = 'travel_todo_list'

    #---------------------------------------------------------------------------
    def get_absolute_url(self):
        return reverse('travel-todo', args=[self.id])

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return u'%s' % self.title



#===============================================================================
class ProfileManager(models.Manager):
    
    #---------------------------------------------------------------------------
    def public(self):
        return self.filter(access=self.model.Access.PUBLIC).exclude(user__id=1)


#===============================================================================
class Profile(models.Model):
    
    #===========================================================================
    class Access(ChoiceEnumeration):
        PUBLIC    = ChoiceEnumeration.Option('PUB',  'Public', default=True)
        PRIVATE   = ChoiceEnumeration.Option('PRI',  'Private')
        PROTECTED = ChoiceEnumeration.Option('PRO',  'Protected')
    
    user   = models.OneToOneField(User, related_name='travel_profile')
    access = models.CharField(
        max_length=3, 
        choices=Access.CHOICES,
        default=Access.DEFAULT
    )
    
    objects = ProfileManager()
    
    #---------------------------------------------------------------------------
    def public_url(self):
        return reverse('travel-profile', args=[self.user.username])

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return unicode(self.user)
        
    #---------------------------------------------------------------------------
    def history(self):
        return TravelLog.objects.history(self.user)
    
    #---------------------------------------------------------------------------
    def history_json(self):
        return TravelLog.objects.history_json(self.user)
    
    #---------------------------------------------------------------------------
    def history_details(self):
        history = list(self.history())
        countries = sorted(
            set([(h.entity.name, h.entity.code) for h in history if h.entity.type.abbr == 'co']),
            key=lambda e: e[0]
        )
        
        return {'history': history, 'countries': countries}
        
    #---------------------------------------------------------------------------
    is_public    = property(lambda self: self.access == self.Access.PUBLIC)
    is_private   = property(lambda self: self.access == self.Access.PRIVATE)
    is_protected = property(lambda self: self.access == self.Access.PROTECTED)


#-------------------------------------------------------------------------------
def profile_factory(sender, instance, created=False, **kws):
        if created:
            Profile.objects.get_or_create(user=instance)


models.signals.post_save.connect(profile_factory, sender=User)


#===============================================================================
class EntityType(models.Model):
    abbr  = models.CharField(max_length=4, db_index=True)
    title = models.CharField(max_length=25)

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return self.title


#===============================================================================
class EntityManager(models.Manager):

    RELATIONSHIP_MAP = {'co': 'country', 'st': 'state', 'cn': 'continent'}
    
    #---------------------------------------------------------------------------
    def search(self, term, type=None):
        term = term.strip()
        qs = self.filter(type__abbr=type) if type else self.all()
        if not term:
            return qs
        
        return qs.filter(
            models.Q(name__icontains=term)      |
            models.Q(full_name__icontains=term) |
            models.Q(locality__icontains=term)  |
            models.Q(code__iexact=term)
        )
    
    #---------------------------------------------------------------------------
    def related_entities(self, entity):
        relationship = self.RELATIONSHIP_MAP.get(entity.type.abbr)
        if relationship:
            cursor = connection.cursor()
            cursor.execute(
                '''SELECT et.`abbr`, COUNT(t.`type_id`)
                     FROM `travel_entity` AS t
               INNER JOIN `travel_entitytype` AS et ON t.`type_id` = et.id 
                    WHERE t.`%s_id` = %%s
                 GROUP BY t.`type_id` ''' % (relationship,),
                [entity.id]
            )
            return cursor.fetchall()
            
        return ()
        
    #---------------------------------------------------------------------------
    def countries(self):
        return self.filter(type__abbr='co')
    
    #---------------------------------------------------------------------------
    def country(self, code):
        return self.get(code=code, type__abbr='co')

    #---------------------------------------------------------------------------
    def country_dict(self):
        return dict([(e.code, e) for e in self.countries()])


#-------------------------------------------------------------------------------
def wikipedia_url(entity):
    return WIKIPEDIA_URL % travel_utils.nice_url(entity.full_name)


#-------------------------------------------------------------------------------
def world_heritage_url(entity):
    return WORLD_HERITAGE_URL % entity.code


_default_external_handler = ('Wikipedia', wikipedia_url)
_external_url_handlers = {
    'wh': ('UNESCO', world_heritage_url)
}


#===============================================================================
class Entity(models.Model):
    
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
    type      = models.ForeignKey(EntityType)
    code      = models.CharField(max_length=6, db_index=True)
    name      = models.CharField(max_length=175)
    full_name = models.CharField(max_length=175)
    lat       = models.DecimalField(max_digits=7, decimal_places=4, default='0.0')
    lon       = models.DecimalField(max_digits=7, decimal_places=4, default='0.0')
    category  = models.CharField(blank=True, max_length=4)
    locality  = models.CharField(max_length=256, blank=True)

    flag      = models.ForeignKey(Flag, null=True, blank=True,on_delete=models.SET_NULL)
    capital   = models.ForeignKey('self', related_name='capital_set',   blank=True, null=True)
    state     = models.ForeignKey('self', related_name='state_set',     blank=True, null=True)
    country   = models.ForeignKey('self', related_name='country_set',   blank=True, null=True)
    continent = models.ForeignKey('self', related_name='continent_set', blank=True, null=True)
    tz        = models.CharField('timezone', max_length=40, blank=True)
    #extras    = models.TextField(blank=True)

    objects   = EntityManager()
    
    RELATED_DETAILS = {
        'co': 'Countries',
        'st': 'States, provinces, territories, etc',
        'ct': 'Cities',
        'ap': 'Airports',
        'np': 'National Parks',
        'lm': 'Landmarks',
        'wh': 'World Heriage Sites',
    }
    
    #===========================================================================
    class Meta:
        ordering = ('name',)

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return self.name
    
    #---------------------------------------------------------------------------
    def _permalink_args(self):
        code = self.code or self.id
        if self.type.abbr in ('st', 'wh'):
            code = (
                '%s-%s' % (self.country.code, code)
                if self.country
                else code
            )
        
        return [self.type.abbr, code]
        
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
    @property
    def timezone(self):
        if not hasattr(self, '__timezone'):
            timezone = self.tz
            if not timezone and self.state:
                timezone = self.state.timezone
            if not timezone and self.country:
                timezone = self.country.timezone
            self.__timezone = timezone
        return self.__timezone
        
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
            return Entity.Subnational.CHOICES_DICT.get(self.category, self.type.title)
            
        return self.type.title
    
    #---------------------------------------------------------------------------
    @property
    def related_entities(self):
        rels = Entity.objects.related_entities(self)
        return [
            {'abbr': abbr, 'text': self.RELATED_DETAILS[abbr], 'count': cnt}
            for abbr, cnt in rels
        ]
        
    #---------------------------------------------------------------------------
    @property
    def flag_dir(self):
        abbr = self.type.abbr
        if abbr == 'co' or abbr == 'ct':
            return abbr
        elif abbr == 'st' and self.country:
            return 'st/%s' % (self.country.code.lower(), )
        return ''
    
    #---------------------------------------------------------------------------
    def related_by_type(self, type):
        key = Entity.objects.RELATIONSHIP_MAP[self.type.abbr]
        return Entity.objects.filter(models.Q(**{key: self}), type=type)
        
    #---------------------------------------------------------------------------
    def update_flags(self, flag_url, sizes=None):
        if self.flag and not self.flag.is_locked:
            flag = self.flag
        else:
            flag = Flag()

        data = Flag.objects.get_flag_data_by_sizes(flag_url, sizes=sizes)
        flag.set_flags(flag_url, self.flag_dir, self.code, data)
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
            return GOOGLE_MAPS_LATLON % (self.lat, self.lon)
        else:
            return GOOGLE_MAPS % (travel_utils.nice_url(self.name),)


#===============================================================================
class EntityExtraType(models.Model):
    abbr  = models.CharField(max_length=4, db_index=True)
    descr = models.CharField(max_length=25)


#===============================================================================
class EntityExtra(models.Model):
    entity = models.ForeignKey(Entity)
    type = models.ForeignKey(EntityExtraType)
    ref = models.TextField()


#-------------------------------------------------------------------------------
def custom_sql_as_dict(sql, args):
    cursor = connection.cursor()
    cursor.execute(sql, args)
    description = cursor.description
    return [
        dict(zip([column[0] for column in description], row))
        for row in cursor.fetchall()
    ]


#===============================================================================
class TravelLogManager(models.Manager):
    
    DETAILED_HISTORY_SQL = '''SELECT
              log.id, 
              log.entity_id,
              entity.code,
              entity.name,
              entity.locality,
              entity_co.name AS country_name,
              entity_co.code AS country_code,
              CONCAT('{media}', flag_co.width_16) AS flag_co_url,
              MIN(log.rating) AS rating,
              UNIX_TIMESTAMP(MAX(log.arrival)) * 1000 AS most_recent_visit,
              UNIX_TIMESTAMP(MIN(log.arrival)) * 1000 AS first_visit,
              COUNT(log.entity_id) AS num_visits,
              etype.abbr AS type_abbr,
              etype.title AS type_title,
              CONCAT('{media}', flag.width_32) AS flag_url
         FROM `travel_travellog`  AS log
    LEFT JOIN `travel_entity`     AS entity    ON log.entity_id     = entity.id
    LEFT JOIN `travel_entity`     AS entity_co ON entity.country_id = entity_co.id
    LEFT JOIN `travel_entitytype` AS etype     ON entity.type_id    = etype.id
    LEFT JOIN `travel_flag`       AS flag      ON entity.flag_id    = flag.id
    LEFT JOIN `travel_flag`       AS flag_co   ON entity_co.flag_id = flag_co.id
        WHERE `user_id` = %s
     GROUP BY `entity_id`
     ORDER BY most_recent_visit DESC'''.format(media=settings.MEDIA_URL)
    
    #---------------------------------------------------------------------------
    def history(self, user):
        return self.raw(
            '''SELECT   *, 
                        MAX(arrival) AS most_recent_visit,
                        MIN(arrival) AS first_visit,
                        COUNT(entity_id) AS num_visits
                 FROM   `travel_travellog`
                WHERE   `user_id` = %s
             GROUP BY   `entity_id`
             ORDER BY   most_recent_visit DESC''',
             [user.id]
        )
    
    #---------------------------------------------------------------------------
    def _detailed_history(self, user):
        return custom_sql_as_dict(self.DETAILED_HISTORY_SQL, [user.id])

    #---------------------------------------------------------------------------
    def history_json(self, user):
        results = travel_utils.json_dumps(self._detailed_history(user))
        return results

    #---------------------------------------------------------------------------
    def recent_countries(self, user):
        return self.raw(
            '''SELECT   tl.*, MIN(tl.arrival) AS most_recent_visit
                 FROM   `travel_travellog` tl
           INNER JOIN   `travel_entity` e on tl.entity_id = e.id
                WHERE   `user_id` = %s AND `e`.`type_id` = 2
             GROUP BY   `entity_id`
             ORDER BY   most_recent_visit DESC''',
             [user.id]
        )
    
    #---------------------------------------------------------------------------
    def checklist(self, user):
        return dict(
            self.filter(user=user).values_list('entity').annotate(count=models.Count('entity'))
        )



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
    entity = models.ForeignKey(Entity)
    
    objects = TravelLogManager()
    
    #===========================================================================
    class Meta:
        get_latest_by = 'arrival'
        ordering = ('-arrival',)

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return u'%s | %s' % (self.entity, self.user)

    #---------------------------------------------------------------------------
    def get_absolute_url(self):
        return reverse('travel-log-entry', args=[self.user.username, self.id])
    
    #---------------------------------------------------------------------------
    def save(self, *args, **kws):
        self.arrival = self.arrival or datetime.now()
        return super(TravelLog, self).save(*args, **kws)
    
    #---------------------------------------------------------------------------
    def update_notes(self, note):
        self.notes = note
        self.save()



#===============================================================================
class Currency(models.Model):
    iso = models.CharField(max_length=4, primary_key=True)
    name = models.CharField(max_length=50)
    fraction = models.CharField(blank=True, max_length=8)
    fraction_name = models.CharField(blank=True, max_length=15)
    sign = models.CharField(blank=True, max_length=4)
    alt_sign = models.CharField(blank=True, max_length=4)

    def __unicode__(self):
        return self.name


#===============================================================================
class EntityInfo(models.Model):
    entity = models.OneToOneField(Entity)
    iso3 = models.CharField(blank=True, max_length=3)
    currency = models.ForeignKey(Currency, blank=True, null=True)
    denom = models.CharField(blank=True, max_length=40)
    denoms = models.CharField(blank=True, max_length=60)
    languages = models.CharField(blank=True, max_length=100)
    phone = models.CharField(blank=True, max_length=20)
    electrical = models.CharField(blank=True, max_length=40)
    postal_code = models.CharField(blank=True, max_length=60)
    neighbors = models.CharField(blank=True, max_length=50)
    tld = models.CharField(blank=True, max_length=8)
    population = models.CharField(blank=True, max_length=12)
    area = models.CharField(blank=True, max_length=10)

    #---------------------------------------------------------------------------
    def electrical_info(self):
        if self.electrical:
            v,h,p = self.electrical.split('/')
            return {'volts': v, 'hertz': h, 'plugs': p.split(',')}
        return {}

