from django import http
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

from travel import models as travel
from travel import forms
from travel import utils


#-------------------------------------------------------------------------------
def all_profiles(request):
    return render(request, 'travel/profile/all.html', {
        'profiles': travel.Profile.objects.public()
    })


#-------------------------------------------------------------------------------
def profile(request, username):
    return render(request, 'travel/profile/profile.html', {
        'profile': get_object_or_404(travel.Profile, user__username=username)
    })


#-------------------------------------------------------------------------------
def todo_lists(request):
    return render(request, 'travel/todo/listing.html', {
        'todos': travel.ToDoList.objects.for_user(request.user)
    })


#-------------------------------------------------------------------------------
def todo_list(request, pk):
    todo = get_object_or_404(travel.ToDoList, pk=pk)
    done, entities = todo.user_results(request.user)
    return render(request, 'travel/todo/detail.html', {
        'todo': todo,
        'entities': entities,
        'stats': {'total': len(entities), 'done': done}
    })


#-------------------------------------------------------------------------------
def search(request):
    search_form = forms.SearchForm(request.GET)
    data = {'search_form': search_form}
    if search_form.is_valid():
        q = search_form.cleaned_data['search']
        by_type = search_form.cleaned_data['type']
        data.update(search=q, results=travel.Entity.objects.search(q, by_type))

    return render(request, 'travel/search/search.html', data)


#-------------------------------------------------------------------------------
@login_required
def search_advanced(request):
    # 'travel-search-advanced'
    data = {'results': None, 'search': ''}
    search = request.GET.get('search', '').strip()
    if search:
        lines = [line.strip() for line in search.splitlines()]
        data.update(
            search='\n'.join(lines),
            results=travel.Entity.objects.advanced_search(lines)
        )
        
    return render(request, 'travel/search/advanced.html', data)


#-------------------------------------------------------------------------------
def by_locale(request, ref):
    etype = get_object_or_404(travel.EntityType, abbr=ref)
    data = {'type': etype, 'places': etype.entity_set.all()}
    return render(request, 'travel/entities/%s-listing.html' % ref, data)


#-------------------------------------------------------------------------------
def _entity_base(request, entity):
    if request.user.is_authenticated():
        history = request.user.travellog_set.filter(entity=entity)
        if request.method == 'POST':
            form = forms.TravelLogForm(request.POST)
            if form.is_valid():
                form.save(request.user, entity)
                return http.HttpResponseRedirect(request.path)
        else:
            form = forms.TravelLogForm()
    else:
        form = None
        history = []

    template = 'travel/entities/%s-detail.html' % entity.type.abbr
    return render(
        request,
        [template, 'travel/entities/detail-base.html'],
        {'place': entity, 'form': form, 'history': history}
    )


#-------------------------------------------------------------------------------
def _handle_entity(request, ref, code, aux, handler):
    if aux:
        entity = travel.Entity.objects.filter(type__abbr=ref, country__code=code, code=aux)
    else:
        entity = travel.Entity.objects.filter(type__abbr=ref, code=code)

    n = len(entity)
    if n == 0:
        raise http.Http404
    elif n > 1:
        return render(request, 'travel/search/search.html', {'results': entity})
    else:
        return handler(request, entity[0])


#-------------------------------------------------------------------------------
def entity(request, ref, code, aux=None):
    return _handle_entity(request, ref, code, aux, _entity_base)


#-------------------------------------------------------------------------------
def entity_relationships(request, ref, code, rel):
    places = travel.Entity.objects.filter(type__abbr=ref, code=code)
    count  = places.count()
    
    if count == 0:
        raise http.Http404('No entity matches the given query.')
    elif count > 1:
        return render(request, 'travel/search/search.html', {'results': places})

    place = places[0]
    etype  = get_object_or_404(travel.EntityType, abbr=rel)
    return render(request, 'travel/entities/%s-listing.html' % rel, {
        'type': etype,
        'places': place.related_by_type(etype),
        'parent': place
    })


#-------------------------------------------------------------------------------
def log_entry(request, username, pk):
    entry = get_object_or_404(travel.TravelLog, user__username=username, pk=pk)
    if request.user == entry.user:
        if request.method == 'POST':
            form = forms.TravelLogForm(request.POST, instance=entry)
            if form.is_valid():
                form.save(user=request.user)
                return http.HttpResponseRedirect(request.path)
        else:
            form = forms.TravelLogForm(instance=entry)
    else:
        form = None
    
    return render(request, 'travel/log-entry.html', {'entry': entry, 'form':  form})

################################################################################
#
# Admin utils below
#
################################################################################


#-------------------------------------------------------------------------------
def _entity_edit(request, entity):
    if request.method == 'POST':
        form = forms.EditEntityForm(request.POST, instance=entity)
        if form.is_valid():
            form.save()
            return http.HttpResponseRedirect(entity.get_absolute_url())
    else:
        form = forms.EditEntityForm(instance=entity)

    return render(
        request,
        'travel/entities/edit.html',
        {'place': entity, 'form': form}
    )


#-------------------------------------------------------------------------------
@utils.superuser_required
def entity_edit(request, ref, code, aux=None):
    return _handle_entity(request, ref, code, aux, _entity_edit)


#-------------------------------------------------------------------------------
@utils.superuser_required
def start_add_entity(request):
    abbr = request.GET.get('type')
    if abbr:
        if abbr == 'co':
            return http.HttpResponseRedirect(reverse('travel-entity-add-co'))
            
        co = request.GET.get('country')
        if co:
            return http.HttpResponseRedirect(
                reverse('travel-entity-add-by-co', args=(co, abbr))
            )
    
    entity_types = travel.EntityType.objects.exclude(abbr__in=['cn', 'co'])
    return render(
        request,
        'travel/entities/add/start.html',
        {'types': entity_types, 'countries': travel.Entity.objects.countries()}
    )


#-------------------------------------------------------------------------------
@utils.superuser_required
def add_entity_co(request):
    entity_type = get_object_or_404(travel.EntityType, abbr='co')
    if request.method == 'POST':
        form = forms.NewCountryForm(request.POST)
        if form.is_valid():
            entity = form.save(entity_type)
            return http.HttpResponseRedirect(entity.get_absolute_url())
    else:
        form = forms.NewCountryForm()
        
    return render(
        request,
        'travel/entities/add/add.html',
        {'form': form, 'entity_type': entity_type}
    )


#-------------------------------------------------------------------------------
@utils.superuser_required
def add_entity_by_co(request, code, abbr):
    entity_type = get_object_or_404(travel.EntityType, abbr=abbr)
    country = travel.Entity.objects.get(code=code, type__abbr='co')

    if request.method == 'POST':
        form = forms.NewEntityForm(request.POST)
        if form.is_valid():
            entity = form.save(entity_type, country=country)
            return http.HttpResponseRedirect(entity.get_absolute_url())
    else:
        form = forms.NewEntityForm()
    
    return render(request, 'travel/entities/add/add.html', {
        'entity_type': entity_type,
        'form': form
    })
