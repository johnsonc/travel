import re
from datetime import datetime
from urllib import quote_plus

from django.conf import settings
from django.db import models, connection
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from path import path
from jargon.utils.json_utils import dumps as json_dumps
from jargon.db.fields import ChoiceEnumeration
from jargon.apps.annotation.models import Markup

GOOGLE_MAPS        = 'http://maps.google.com/maps?q=%s'
GOOGLE_MAPS_LL     = 'http://maps.google.com/maps?q=%s,+%s&iwloc=A&z=10'
GOOGLE_SEARCH_URL  = 'http://www.google.com/search?as_q=%s'
WIKIPEDIA_URL      = 'http://en.wikipedia.org/wiki/Special:Search?search=%s&go=Go'
WORLD_HERITAGE_URL = 'http://whc.unesco.org/en/list/%s'

BASE_FLAG_DIR = path('img/flags')
STAR          = mark_safe('&#9733;')

_world_heritage_category = {
    'C': 'Cultural',
    'N': 'Natural',
    'M': 'Mixed'
}

#-------------------------------------------------------------------------------
def flag_upload(size):
    def upload_func(instance, filename):
        name = '%s-%s%s' % (instance.ref, size, path(filename).ext)
        return BASE_FLAG_DIR / ('%s/%s' % (instance.base_dir, name))
    return upload_func


#===============================================================================
class FlagManager(models.Manager):
    
    flag_url_re =  re.compile(r'(.*)/(\d+)px(.*)')

    #---------------------------------------------------------------------------
    def get_wiki_flags_by_size(self, url, sizes=None):
        '''Typical url format:
        
        http://upload.wikimedia.org/wikipedia/commons/thumb/x/yz/Flag_of_XYZ.svg/120px-Flag_of_XYZ.svg.png'''
        import requests

        sizes = sizes or ('16', '32', '64', '128', '256', '512')
        data = {}
        for size in sizes:
            size_url = self.flag_url_re.sub(r'\1/%spx\3' % size, url)
            r = requests.get(size_url)
            if r.status_code != 200:
                raise ValueError('Status %s (%s)' % (r.status_code, size_url))

            data[size] = r.content

        return data


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
        #HACK - fixme!
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
    @models.permalink
    def get_absolute_url(self):
        return ('travel-todo', [self.id])

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return u'%s' % self.title



EXTRA_INFO = { 'ap': 'IATA'}

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
    @models.permalink
    def public_url(self):
        return ('travel-profile', [self.user.username])

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
        
        return {
            'history': history,
            'countries': countries
        }
        
    #---------------------------------------------------------------------------
    is_public    = property(lambda self: self.access == self.Access.PUBLIC)
    is_private   = property(lambda self: self.access == self.Access.PRIVATE)
    is_protected = property(lambda self: self.access == self.Access.PROTECTED)


#-------------------------------------------------------------------------------
def profile_factory(sender, instance, created=False, **kws):
        if created:
            Profile.objects.create(user=instance)


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

    RELATIONSHIP_MAP = {
        'co': 'country',
        'st': 'state',
        'cn': 'continent',
    }
    
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
    def country_dict(self):
        return dict([(e.code, e) for e in self.countries()])


#-------------------------------------------------------------------------------
def wikipedia_url(entity):
    return WIKIPEDIA_URL % quote_plus(entity.full_name.encode('utf8'))


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

    old_id    = models.IntegerField(default=0)
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

    objects = EntityManager()
    
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
    @models.permalink
    def get_absolute_url(self):
        # url(r'^i/(\w+)/(\w+)/(\w+)/(\w+)/$'
        return ('travel-entity', self._permalink_args())

    #---------------------------------------------------------------------------
    @models.permalink
    def get_edit_url(self):
        # url(r'^edit/i/(\w+)/(\w+)/(\w+)/(\w+)/$'
        return ('travel-entity-edit', self._permalink_args())
    
    #---------------------------------------------------------------------------
    def wikipedia_search_url(self):
        return WIKIPEDIA_URL % quote_plus(self.full_name.encode('utf8'))

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
            return _world_heritage_category[self.category]
            
        return self.category

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
    def update_flags(self, flag_url, sizes=None):
        if self.flag and not self.flag.is_locked:
            flag = self.flag
        else:
            flag = Flag()

        data = Flag.objects.get_wiki_flags_by_size(flag_url, sizes=sizes)
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
            return GOOGLE_MAPS_LL % (self.lat, self.lon)
        else:
            return GOOGLE_MAPS % (quote_plus(self.name.encode('UTF8')),)



#===============================================================================
class TravelLogManager(models.Manager):
    
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
    def history_json(self, user):
        cursor = connection.cursor()
        cursor.execute(
            '''SELECT tl.id, 
                      tl.entity_id,
                      te.code,
                      te.name,
                      tej.name AS country_name,
                      tej.code AS country_code,
                      tl.rating AS rating, 
                      UNIX_TIMESTAMP(MAX(tl.arrival)) * 1000 AS most_recent_visit,
                      UNIX_TIMESTAMP(MIN(tl.arrival)) * 1000 AS first_visit,
                      COUNT(tl.entity_id) AS num_visits,
                      tet.abbr AS type_abbr,
                      tet.title AS type_title,
                      tf.width_32 AS flag_url
                 FROM `travel_travellog` AS tl
            LEFT JOIN `travel_entity` AS te ON tl.entity_id = te.id
            LEFT JOIN `travel_entity` AS tej ON te.country_id = tej.id
            LEFT JOIN `travel_entitytype` AS tet ON te.type_id = tet.id
            LEFT JOIN `travel_flag` AS tf ON te.flag_id = tf.id 
                WHERE `user_id` = %s
             GROUP BY `entity_id`
             ORDER BY most_recent_visit DESC''',
             [user.id]
        )

        desc = cursor.description
        return json_dumps(
            [dict(zip([c[0] for c in desc], r)) for r in cursor.fetchall()]
        )

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
    notes = models.ForeignKey(Markup, null=True, blank=True)
    entity = models.ForeignKey(Entity)
    
    objects = TravelLogManager()
    
    #===========================================================================
    class Meta:
        get_latest_by = ('arrival',)
        ordering = ('-arrival',)

    #---------------------------------------------------------------------------
    def __unicode__(self):
        return u'%s | %s' % (self.entity, self.user)

    #---------------------------------------------------------------------------
    @models.permalink
    def get_absolute_url(self):
        return ('travel-log-entry', [self.user.username, self.id])
    
    #---------------------------------------------------------------------------
    def save(self, *args, **kws):
        self.arrival = self.arrival or datetime.now()
        return super(TravelLog, self).save(*args, **kws)
    
    #---------------------------------------------------------------------------
    def update_notes(self, note):
        if note:
            if self.notes:
                self.notes.text = note
                self.notes.save()
            else:
                self.notes = Markup.objects.create(format=Markup.Format.BASIC, text=note)
                self.save()
        else:
            if self.notes:
                self.notes.delete()
            
            self.notes = None
            self.save()
    
