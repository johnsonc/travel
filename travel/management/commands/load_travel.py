import sys
import codecs
from pprint import pprint
from optparse import make_option
from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from travel import models as travel


#-------------------------------------------------------------------------------
def read_entities(fn, delimiter='|'):
    lines = []
    with codecs.open(fn, encoding='utf-8') as fp:
        lineno = 0
        for line in fp:
            lineno += 1
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append((lineno, tuple(line.split(delimiter))))
                
    return lines


#===============================================================================
class TravelEntityCache(object):
    
    #---------------------------------------------------------------------------
    def __init__(self):
        self.cache = {}
        
    #---------------------------------------------------------------------------
    def __getitem__(self, key):
        '''
            `key` should be a tuple of (type__abbr,code)
        '''
        if not key in self.cache:
            print 'Getting', key
            self.cache[key] = travel.TravelEntity.objects.get(type__abbr=key[0], code=key[1])
            
        return self.cache[key]


#===============================================================================
class TravelEntityLoader(object):
    
    #---------------------------------------------------------------------------
    def __init__(self):
        self.types = dict([(et.abbr, et) for et in travel.TravelEntityType.objects.all()]
        self.cache = TravelEntityCache()
    
    #---------------------------------------------------------------------------
    def create_flag(self, entity, flag_url):
        print u'Retrieving flag for %s' % (flag_url, )
        try:
            entity.update_flags(flag_url)
        except Exception, why:
            print 'Error updating flag'
            print why

    #---------------------------------------------------------------------------
    def create_city(self, co, st, name, full_name=''):
        city, new = travel.TravelEntity.objects.get_or_create(
            type=self.types['ct'],
            name=name,
            country=co,
        )
        
        if new:
            city.full_name = full_name or name
            city.state     = st
            city.code      = '%d' % city.id
            city.save()
        
        print 'Got %s city %s' % ('new' if new else 'old', city)
        return city
        
    #-------------------------------------------------------------------------------
    def create_st(co, fields):
        name, full_name, code, cat, capital, flag_url = fields
        print 'Creating %s...' % name
    
        attrs = dict(
            name      = name,
            full_name = full_name or name,
            category  = cat
        )
    
        print 'Attrs', attrs
        subnat, new = travel.TravelEntity.objects.get_or_create(
            type=self.types['st'],
            country=co,
            code=code,
            defaults=attrs
        )

        print 'Got %s %s: %s' % ('new' if new else 'old', subnat.category_detail, subnat)
        if capital:
            subnat.capital = self.create_city(co, subnat, capital)
            subnat.save()
        
        if flag_url:
            self.create_flag(subnat, flag_url)
        
        return subnat

    #-------------------------------------------------------------------------------
    def process_entity_file(filename, delimiter='|'):
        #co|NL|st|South Holland||ZH|P|The Hague|http://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Flag_Zuid-Holland.svg/27px-Flag_Zuid-Holland.svg.png
        lines = read_entities(filename, delimiter)
        print 'File:', filename, 'Lines:', len(lines)
    
        for lineno, data in lines:
            if len(data) < 5:
                print 'Bad line #%d: %s' % (lineno, data)
            else:
                keys, kind, fields = data[:2], data[2], data[3:]
                handler = _entity_creation_handlers.get(kind)
                if kind == 'st':
                    parent = self.cache[keys]
                    entity = self.create_st(parent, fields)
                    print 'TravelEntity: %s' % entity
                
                else:
                    print 'Skipped: %s, Line  #%d' % (kind, lineno)

            print '-' * 40


#===============================================================================
class Command(BaseCommand):
    help = ' '.join([line.strip() for line in __doc__.strip().splitlines()])

    #---------------------------------------------------------------------------
    def handle(self, *args, **options):
        loader = TravelEntityLoader()
        for arg in args:
            loader.process_entity_file(arg)
        
