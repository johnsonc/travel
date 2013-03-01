from travel import forms

def search(request):
    return {
        'search_form': forms.SearchForm()
    }