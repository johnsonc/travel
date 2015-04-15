from django.core.management.base import BaseCommand, CommandError
from travel.models import TravelLog
from django.contrib.auth.models import User
from pprint import pprint

#===============================================================================
class Command(BaseCommand):
    help = ''

    #---------------------------------------------------------------------------
    def handle(self, *args, **options):
        for arg in args:
            user = User.objects.get(username=arg)
            history = TravelLog.objects.user_history(user)
            print '#' * 40
            history = list(history)
            for e in history:
                pprint(e)
            print len(history)

            