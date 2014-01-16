from travel import forms
from travel.models import TravelLog


#-------------------------------------------------------------------------------
def _checklist(user):
    return TravelLog.objects.checklist(user) if user.is_authenticated() else {}


#-------------------------------------------------------------------------------
def search(request):
    return {
        'search_form': forms.SearchForm(),
        'checklist': _checklist(request.user)
    }