from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django import http

from jargon.shortcuts import request_to_response
from travel import models as travel
from travel import forms
from travel import utils


#-------------------------------------------------------------------------------
def _get_entity(ref, code):
    return get_object_or_404(travel.Entity, type__abbr=ref, code=code)


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
def by_locale(request, ref):
    etype = get_object_or_404(travel.EntityType, abbr=ref)
    data = {'type': etype, 'places': etype.entity_set.all()}
    return request_to_response(request, 'travel/entities/%s-listing.html' % ref, data)


#-------------------------------------------------------------------------------
def flag_upload(request, ref, code):
    try:
        utils.flag_from_wikimedia(_get_entity(ref, code), request.POST['url'])
    except Exception, why:
        msg = '%s' % why
    else:
        msg = 'Successfully added flag images'
        
    request.user.message_set.create(message=msg)
    return http.HttpResponseRedirect(request.path)


#-------------------------------------------------------------------------------
def entity(request, ref, code):
    place = _get_entity(ref, code)
    if request.method == 'POST':
        form = forms.TravelLogForm(place, request.POST)
        if form.is_valid():
            form.save(request.user)
            return http.HttpResponseRedirect(request.path)
    else:
        form = forms.TravelLogForm(place)
        
    return request_to_response(
        request,
        ['travel/entities/%s-detail.html' % ref, 'travel/entities/detail-base.html'],
        {'place': place, 'form': form}
    )

#-------------------------------------------------------------------------------
def entity_relationship(request, ref, code, rel):
    place  = _get_entity(ref, code)
    etype  = get_object_or_404(travel.EntityType, abbr=rel)
    key    = travel.Entity.objects.RELATIONSHIP_MAP[ref]
    places = travel.Entity.objects.filter(models.Q(**{key: place}), type__abbr=rel)
    data   = {'type': etype, 'places': places, 'parent': place}
    return request_to_response(request, 'travel/entities/%s-listing.html' % rel, data)
    