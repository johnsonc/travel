from datetime import datetime
from urllib import quote_plus

from django.db import models, connection
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from path import path
from jargon.db.fields import ChoiceEnumeration
from jargon.apps.annotation.models import Markup

GOOGLE_MAPS       = 'http://maps.google.com/maps?q=%s'
GOOGLE_MAPS_LL    = 'http://maps.google.com/maps?q=%s,+%s&iwloc=A&z=10'
GOOGLE_SEARCH_URL = 'http://www.google.com/search?as_q=%s'
WIKIPEDIA_URL     = 'http://en.wikipedia.org/wiki/Special:Search?search=%s&go=Go'
BASE_FLAG_DIR     = path('img/flags')
STAR              = mark_safe('&#9733;')


#-------------------------------------------------------------------------------
def flag_upload(size):
    def upload_func(instance, filename):
        name = '%s-%s%s' % (instance.ref, size, path(filename).ext)
        return BASE_FLAG_DIR / ('%s/%s' % (instance.base_dir, name))
    return upload_func


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


STATE        = 'S'
PROVINCE     = 'P'
DISTRICT     = 'D'
TERRITORY    = 'T'
COMMONWEALTH = 'W'
COUNTY       = 'C'
REGION       = 'R'

STATE_OPTS_DICT = {
    STATE:        _('State'),
    PROVINCE:     _('Province'),
    DISTRICT:     _('District'),
    TERRITORY:    _('Territory'),
    COMMONWEALTH: _('Commonwealth'),
    COUNTY:       _('County'),
    REGION:       _('Region'),
}

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


#===============================================================================
class Entity(models.Model):
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
    def _permalink_url(self, name):
        type_abbr = self.type.abbr
        code = self.code or self.id
        if type_abbr in ('st', 'wh'):
            code = (
                '%s-%s' % (self.country.code, code)
                if self.country
                else code
            )
        
        return (name, [type_abbr, code])
        
    #---------------------------------------------------------------------------
    @models.permalink
    def get_absolute_url(self):
        # url(r'^i/(\w+)/(\w+)/(\w+)/(\w+)/$'
        return self._permalink_url('travel-entity')

    #---------------------------------------------------------------------------
    @models.permalink
    def get_edit_url(self):
        # url(r'^edit/i/(\w+)/(\w+)/(\w+)/(\w+)/$'
        return self._permalink_url('travel-entity-edit')
    
    #---------------------------------------------------------------------------
    def wikipedia_search_url(self):
        return WIKIPEDIA_URL % quote_plus(self.full_name.encode('utf8'))

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
            return STATE_OPTS_DICT.get(self.category, self.type.title)
            
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
        if abbr == 'co':
            return '%s' % (self.type.abbr,)
        elif abbr == 'st' and self.country:
            return '%s/%s' % (self.type.abbr, self.country.code.lower())
        return ''
        
    
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
    
