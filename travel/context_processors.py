from travel import forms
from travel.models import TravelLog
from django.contrib.sites.models import Site


#-------------------------------------------------------------------------------
def _checklist(user):
    return TravelLog.objects.checklist(user) if user.is_authenticated() else {}


#-------------------------------------------------------------------------------
def search(request):
    return {
        'site': Site.objects.get_current(),
        'search_form': forms.SearchForm(),
        'checklist': _checklist(request.user)
    }