from django.core.management.base import BaseCommand, CommandError
from travel.geocode import reversegc
from pprint import pprint

#===============================================================================
class Command(BaseCommand):
    help = ''

    #---------------------------------------------------------------------------
    def handle(self, *args, **options):
        kind = args[0]
        if kind.isalpha() or (kind[0] == '-' and kind[1:].isalpha()):
            args = args[1:]
        else:
            kind = None
        gd = reversegc.geo_loader('csv') #, kind)
        for arg in args:
            coords = tuple([float(f) for f in arg.split(',')])
            pprint(gd.get(coords))
