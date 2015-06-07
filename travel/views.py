from django import http
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

from travel import models as travel
from travel import forms
from travel import utils


#-------------------------------------------------------------------------------
superuser_required = user_passes_test(
    lambda u: u.is_authenticated() and u.is_active and u.is_superuser
)


#-------------------------------------------------------------------------------
def all_profiles(request):
    return render(request, 'travel/profile/all.html', {
        'profiles': travel.TravelProfile.objects.public()
    })


#-------------------------------------------------------------------------------
def profile(request, username):
    return render(request, 'travel/profile/profile.html', {
        'profile': get_object_or_404(travel.TravelProfile, user__username=username)
    })


#-------------------------------------------------------------------------------
def bucket_lists(request):
    return render(request, 'travel/buckets/listing.html', {
        'bucket_lists': travel.TravelBucketList.objects.for_user(request.user)
    })


#-------------------------------------------------------------------------------
def bucket_list_comparison(request, pk, usernames):
    bucket_list = get_object_or_404(travel.TravelBucketList, pk=pk)
    entities = bucket_list.entities.select_related()
    ids = [e.id for e in entities]
    results = []
    for username in usernames.split('/'):
        results.append({
            'username': username,
            'entities': set(travel.TravelLog.objects.filter(
                user__username=username,
                entity__id__in=ids
            ).values_list('entity__id', flat=True))
        })
    
    return render(request, 'travel/buckets/compare.html', {
        'bucket_list': bucket_list,
        'entities': entities,
        'results': results
    })


#-------------------------------------------------------------------------------
def _bucket_list_for_user(request, bucket_list, user):
    done, entities = bucket_list.user_results(user)
    return render(request, 'travel/buckets/detail.html', {
        'bucket_list': bucket_list,
        'entities': entities,
        'stats': {'total': len(entities), 'done': done}
    })


#-------------------------------------------------------------------------------
def bucket_list(request, pk):
    bucket_list = get_object_or_404(travel.TravelBucketList, pk=pk)
    return _bucket_list_for_user(request, bucket_list, request.user)


#-------------------------------------------------------------------------------
def bucket_list_for_user(request, pk, username):
    user = get_object_or_404(User, username=username)
    bucket_list = get_object_or_404(travel.TravelBucketList, pk=pk)
    return _bucket_list_for_user(request, bucket_list, user)


#-------------------------------------------------------------------------------
def search(request):
    search_form = forms.SearchForm(request.GET)
    data = {'search_form': search_form}
    if search_form.is_valid():
        q = search_form.cleaned_data['search']
        by_type = search_form.cleaned_data['type']
        data.update(search=q, results=travel.TravelEntity.objects.search(q, by_type))

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
            results=travel.TravelEntity.objects.advanced_search(lines)
        )
        
    return render(request, 'travel/search/advanced.html', data)


#-------------------------------------------------------------------------------
def by_locale(request, ref):
    etype = get_object_or_404(travel.TravelEntityType, abbr=ref)
    return render(request, 'travel/entities/%s-listing.html' % ref, {
        'type': etype,
        'places': list(etype.entity_set.select_related(
            'entity', 'flag', 'capital', 'state', 'country', 'continent'
        ))
    })


#-------------------------------------------------------------------------------
def _entity_base(request, entity):
    form, history = None, []
    if request.user.is_authenticated():
        history = request.user.travellog_set.filter(entity=entity)
        if request.method == 'POST':
            form = forms.TravelLogForm(entity, request.POST)
            if form.is_valid():
                form.save(request.user)
                return http.HttpResponseRedirect(request.path)
        else:
            form = forms.TravelLogForm(entity)

    template = 'travel/entities/%s-detail.html' % entity.type.abbr
    return render(
        request,
        [template, 'travel/entities/detail-base.html'],
        {'place': entity, 'form': form, 'history': history}
    )


#-------------------------------------------------------------------------------
def _get_entities(ref, code, aux):
    if aux:
        return travel.TravelEntity.objects.filter(type__abbr=ref, country__code=code, code=aux)

    return travel.TravelEntity.objects.filter(type__abbr=ref, code=code)


#-------------------------------------------------------------------------------
def _handle_entity(request, ref, code, aux, handler):
    entity = _get_entities(reg, code, aux)
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
def entity_relationships(request, ref, code, rel, aux=None):
    places = _get_entities(ref, code, aux)
    count  = places.count()
    
    if count == 0:
        raise http.Http404('No entity matches the given query.')
    elif count > 1:
        return render(request, 'travel/search/search.html', {'results': places})

    place = places[0]
    etype  = get_object_or_404(travel.TravelEntityType, abbr=rel)
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
            form = forms.TravelLogForm(entry.entity, request.POST, instance=entry)
            if form.is_valid():
                form.save(user=request.user)
                return http.HttpResponseRedirect(request.path)
        else:
            form = forms.TravelLogForm(entry.entity, instance=entry)
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
        form = forms.EditTravelEntityForm(request.POST, instance=entity)
        if form.is_valid():
            form.save()
            return http.HttpResponseRedirect(entity.get_absolute_url())
    else:
        form = forms.EditTravelEntityForm(instance=entity)

    return render(
        request,
        'travel/entities/edit.html',
        {'place': entity, 'form': form}
    )


#-------------------------------------------------------------------------------
@superuser_required
def entity_edit(request, ref, code, aux=None):
    return _handle_entity(request, ref, code, aux, _entity_edit)


#-------------------------------------------------------------------------------
@superuser_required
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
    
    entity_types = travel.TravelEntityType.objects.exclude(abbr__in=['cn', 'co'])
    return render(
        request,
        'travel/entities/add/start.html',
        {'types': entity_types, 'countries': travel.TravelEntity.objects.countries()}
    )


#-------------------------------------------------------------------------------
@superuser_required
def add_entity_co(request):
    entity_type = get_object_or_404(travel.TravelEntityType, abbr='co')
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
@superuser_required
def add_entity_by_co(request, code, abbr):
    entity_type = get_object_or_404(travel.TravelEntityType, abbr=abbr)
    country = travel.TravelEntity.objects.get(code=code, type__abbr='co')

    if request.method == 'POST':
        form = forms.NewTravelEntityForm(request.POST)
        if form.is_valid():
            entity = form.save(entity_type, country=country)
            return http.HttpResponseRedirect(entity.get_absolute_url())
    else:
        form = forms.NewTravelEntityForm()
    
    return render(request, 'travel/entities/add/add.html', {
        'entity_type': entity_type,
        'form': form
    })
