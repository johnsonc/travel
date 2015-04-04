import re
import os
import operator
from datetime import datetime

from django.conf import settings
from django.db import models, connection
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from choice_enum import ChoiceEnumeration
import travel.utils as travel_utils


GOOGLE_MAPS             = 'http://maps.google.com/maps?q={}'
GOOGLE_MAPS_LATLON      = 'http://maps.google.com/maps?q={},+{}&iwloc=A&z=10'
GOOGLE_SEARCH_URL       = 'http://www.google.com/search?as_q={}'
WIKIPEDIA_URL           = 'http://en.wikipedia.org/wiki/Special:Search?search={}&go=Go'
WORLD_HERITAGE_URL      = 'http://whc.unesco.org/en/list/{}'
BASE_FLAG_DIR           = 'img/flags'
STAR                    = mark_safe('&#9733;')
WORLD_HERITAGE_CATEGORY = { 'C': 'Cultural', 'N': 'Natural', 'M': 'Mixed' }
EXTRA_INFO              = { 'ap': 'IATA'}


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
class Flag(models.Model):
    source = models.CharField(max_length=255)
    base_dir = models.CharField(max_length=8)
    ref = models.CharField(max_length=6)
    thumb  = models.ImageField(upload_to=flag_upload(32), null=True)
    large = models.ImageField(upload_to=flag_upload(128), null=True)
    svg = models.FileField(upload_to=svg_upload, null=True)

    #---------------------------------------------------------------------------
    @property
    def is_locked(self):
        #TODO **hack** - fixme!
        return False if (self.base_dir or self.ref) else True
    
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

        if not abs_dir.exists():
            abs_dir.makedirs()
        
        self.source   = url
        self.base_dir = base
        self.ref      = ref
        
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
        else:
            self.svg = None
            
        self.save()


#===============================================================================
class ToDoListManager(models.Manager):
    
    #---------------------------------------------------------------------------
    def for_user(self, user):
        q = models.Q(is_public=True)
        if user.is_authenticated:
            q |= models.Q(owner=user)
        return self.filter(q)
        
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
        return self.title

    #---------------------------------------------------------------------------
    def user_results(self, user):
        all_entities = self.entities.all()
        done = 0
        if user.is_authenticated():
            entities = []
            for entity in all_entities:
                logged = entity.travellog_set.filter(user=user).count()
                if logged:
                    done += 1
                entities.append((entity, logged))
        else:
            entities = [(e, 0) for e in all_entities]

        return done, entities


#===============================================================================
class ProfileManager(models.Manager):
    
    #---------------------------------------------------------------------------
    def public(self):
        return self.filter(access=self.model.Access.PUBLIC).exclude(user__id=1)

    #---------------------------------------------------------------------------
    def for_user(self, user):
        p, _ =  self.get_or_create(user=user)
        return p


#===============================================================================
class Profile(models.Model):
    
    #===========================================================================
    class Access(ChoiceEnumeration):
        PUBLIC    = ChoiceEnumeration.Option('PUB',  'Public')
        PRIVATE   = ChoiceEnumeration.Option('PRI',  'Private')
        PROTECTED = ChoiceEnumeration.Option('PRO',  'Protected', default=True)
    
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
    @staticmethod
    def _search_q(term):
        return (
            models.Q(name__icontains=term)      |
            models.Q(full_name__icontains=term) |
            models.Q(locality__icontains=term)  |
            models.Q(code__iexact=term)
        )
        
    #---------------------------------------------------------------------------
    def search(self, term, type=None):
        term = term.strip() if term else term
        qs = None
        if term:
            qs = self.filter(self._search_q(term))
        
        if type:
            qs = qs or self
            qs = qs.filter(type__abbr=type)
            
        return self.none() if qs is None else qs
    
    #---------------------------------------------------------------------------
    def advanced_search(self, bits, type=None):
        qq = reduce(operator.ior, [self._search_q(term) for term in bits])
        qs = self.filter(qq)
        return qs.filter(type__abbr=type) if type else qs
        
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
    return WIKIPEDIA_URL.format(travel_utils.nice_url(entity.full_name))


#-------------------------------------------------------------------------------
def world_heritage_url(entity):
    return WORLD_HERITAGE_URL.format(entity.code)


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
    lat       = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    lon       = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
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
    def _permalink_args(self):
        code = self.code or self.id
        if self.type.abbr in ('st', 'wh'):
            code = '{}-{}'.format(self.country.code, code) if self.country else code
        
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
            return 'st/{}'.format(self.country.code.lower())
        return ''
    
    #---------------------------------------------------------------------------
    def related_by_type(self, type):
        key = Entity.objects.RELATIONSHIP_MAP[self.type.abbr]
        return Entity.objects.filter(models.Q(**{key: self}), type=type)
        
    #---------------------------------------------------------------------------
    def update_flag(self, flag_url):
        flag = self.flag if self.flag and not self.flag.is_locked else Flag()
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
class EntityExtraType(models.Model):
    abbr  = models.CharField(max_length=4, db_index=True)
    descr = models.CharField(max_length=25)


#===============================================================================
class EntityExtra(models.Model):
    entity = models.ForeignKey(Entity)
    type = models.ForeignKey(EntityExtraType)
    ref = models.TextField()


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
              CONCAT('{media}', flag_co.thumb) AS flag_co_url,
              MIN(log.rating) AS rating,
              UNIX_TIMESTAMP(MAX(log.arrival)) * 1000 AS most_recent_visit,
              UNIX_TIMESTAMP(MIN(log.arrival)) * 1000 AS first_visit,
              COUNT(log.entity_id) AS num_visits,
              etype.abbr AS type_abbr,
              etype.title AS type_title,
              CONCAT('{media}', flag.thumb) AS flag_url
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
        return travel_utils.custom_sql_as_dict(self.DETAILED_HISTORY_SQL, [user.id])

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
        return u'{} | {}'.format(self.entity, self.user)

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
class TravelLanguage(models.Model):
    iso639_1 = models.CharField(blank=True, max_length=2)
    iso639_3 = models.CharField(blank=True, max_length=3)
    name     = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name


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
    language_codes = models.CharField(blank=True, max_length=100)
    phone = models.CharField(blank=True, max_length=20)
    electrical = models.CharField(blank=True, max_length=40)
    postal_code = models.CharField(blank=True, max_length=60)
    neighbors = models.CharField(blank=True, max_length=50)
    tld = models.CharField(blank=True, max_length=8)
    population = models.CharField(blank=True, max_length=12)
    area = models.CharField(blank=True, max_length=10)
    languages = models.ManyToManyField(TravelLanguage, blank=True)
    
    #---------------------------------------------------------------------------
    def get_languages(self):
        lang = u', '.join([l.name for l in self.languages.all()])
        if self.language_codes:
            lang = u'{} ({})'.format(lang, self.language_codes)
            
        return lang or 'Unknown'
        
    #---------------------------------------------------------------------------
    def electrical_info(self):
        if self.electrical:
            v,h,p = self.electrical.split('/')
            return {'volts': v, 'hertz': h, 'plugs': p.split(',')}
        return {}

