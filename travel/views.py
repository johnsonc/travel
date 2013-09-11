from django import http
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from jargon.shortcuts import request_to_response
from travel import models as travel
from travel import forms
from travel import utils


#-------------------------------------------------------------------------------
@login_required
def support_request(request, title):
    if request.method == 'POST': 
        form = forms.SupportForm(request.POST)
        if form.is_valid():
            utils.send_message(request.user, title, form.cleaned_data['message'])
            return http.HttpResponseRedirect(reverse('travel-thanks'))
    else:
        form = forms.SupportForm()

    data = {'form': form, 'title': title}
    return request_to_response(request, 'travel/site/support.html', data)


#-------------------------------------------------------------------------------
def all_profiles(request):
    data = {'profiles': travel.Profile.objects.public()}
    return request_to_response(request, 'travel/profile/all.html', data)


#-------------------------------------------------------------------------------
def profile(request, username):
    profile = get_object_or_404(travel.Profile, user__username=username)
    return request_to_response(request, 'travel/profile/profile.html', {'profile': profile})


#-------------------------------------------------------------------------------
def _add_todos(request):
    return request_to_response(request, 'travel/construction.html')


#-------------------------------------------------------------------------------
def todo_lists(request):
    if request.user.is_authenticated():
        todos = travel.ToDoList.objects.all_for_user(request.user)
    else:
        todos = travel.ToDoList.objects.filter(is_public=True)

    return request_to_response(request, 'travel/todo/listing.html', {'todos': todos})


#-------------------------------------------------------------------------------
def todo_list(request, pk):
    todo = get_object_or_404(travel.ToDoList, pk=pk)
    anon = request.user.is_anonymous()
    
    entities = []
    total = done = 0
    for entity in todo.entities.all():
        total += 1
        if anon:
            logged = 0
        else:
            logged = entity.travellog_set.filter(user=request.user).count()
            if logged:
                done += 1
    
        entities.append((entity, logged))
        
    data = {'todo': todo, 'entities': entities, 'stats': {'total': total, 'done': done}}
    return request_to_response(request, 'travel/todo/detail.html', data)


#-------------------------------------------------------------------------------
def search(request):
    search_form = forms.SearchForm(request.GET)
    data        = {'search_form': search_form}
    if search_form.is_valid():
        q                     = search_form.cleaned_data['travel_search']
        mtype                 = search_form.cleaned_data['type']
        data['results']       = travel.Entity.objects.search(q, mtype)
        data['travel_search'] = q

    return request_to_response(request, 'travel/search.html', data)


#-------------------------------------------------------------------------------
def search_advanced(request):
    'travel-search-advanced'
    data = {'results': [], 'search': ''}
    if request.method == 'POST':
        search = request.POST.get('search').strip()
        if search:
            lines = [line.strip() for line in search.splitlines()]
            data['search'] = '\n'.join(lines)
            q = models.Q()
            for term in lines:
                print term
                q |= (
                    models.Q(name__icontains=term)      |
                    models.Q(full_name__icontains=term) |
                    models.Q(locality__icontains=term)  |
                    models.Q(code__iexact=term)
                )
                
            qs = travel.Entity.objects.filter(q)
            print qs.count()
            data['results'] = qs
        
    return request_to_response(request, 'travel/search-advanced.html', data)
    

#-------------------------------------------------------------------------------
def by_locale(request, ref):
    etype = get_object_or_404(travel.EntityType, abbr=ref)
    data = {'type': etype, 'places': etype.entity_set.all()}
    return request_to_response(request, 'travel/entities/%s-listing.html' % ref, data)


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

    return request_to_response(
        request,
        ['travel/entities/%s-detail.html' % entity.type.abbr, 'travel/entities/detail-base.html'],
        {'place': entity, 'form': form, 'history': history}
    )


#-------------------------------------------------------------------------------
def entity(request, ref, code, aux=None):
    if aux:
        entity = travel.Entity.objects.filter(type__abbr=ref, country__code=code, code=aux)
    else:
        entity = travel.Entity.objects.filter(type__abbr=ref, code=code)
        
    n = len(entity)
    if n == 0:
        raise http.Http404
    elif n > 1:
        return request_to_response(request, 'travel/search.html', {'results': entity})
    else:
        entity = entity[0]

    return _entity_base(request, entity)


#-------------------------------------------------------------------------------
def entity_by_parent(request, ref, ref_code, rel, code):
    entity = get_object_or_404(
        travel.Entity,
        country__code=ref_code,
        type__abbr=rel,
        code=code
    )
    return _entity_base(request, entity)


#-------------------------------------------------------------------------------
def entity_relationships(request, ref, code, rel):
    places = travel.Entity.objects.filter(type__abbr=ref, code=code)
    count  = places.count()
    
    if count == 0:
        raise http.Http404('No entity matches the given query.')
    if count > 1:
        return request_to_response(request, 'travel/search.html', {'results': places})
        
    place  = places[0]
    etype  = get_object_or_404(travel.EntityType, abbr=rel)
    key    = travel.Entity.objects.RELATIONSHIP_MAP[ref]
    places = travel.Entity.objects.filter(models.Q(**{key: place}), type__abbr=rel)
    data   = {'type': etype, 'places': places, 'parent': place}
    return request_to_response(request, 'travel/entities/%s-listing.html' % rel, data)


#-------------------------------------------------------------------------------
def log_entry(request, username, pk):
    entry = get_object_or_404(travel.TravelLog, user__username=username, pk=pk)
    if request.user == entry.user:
        if request.method == 'POST':
            form = forms.TravelLogForm(request.POST, instance=entry)
            #import jargon.debug; jargon.debug.set_trace()
            if form.is_valid():
                form.save(user=request.user)
                return http.HttpResponseRedirect(request.path)
        else:
            form = forms.TravelLogForm(instance=entry)
    else:
        form = None
    
    data = {'entry': entry, 'form':  form}
    return request_to_response(request, 'travel/log-entry.html', data)
    