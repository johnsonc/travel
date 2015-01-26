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
def to_template(tmpl):
    def to_template_inner(request):
        return render(request, tmpl)
    return to_template_inner


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
    return render(request, 'travel/site/support.html', data)


#-------------------------------------------------------------------------------
def all_profiles(request):
    data = {'profiles': travel.Profile.objects.public()}
    return render(request, 'travel/profile/all.html', data)


#-------------------------------------------------------------------------------
def profile(request, username):
    profile = get_object_or_404(travel.Profile, user__username=username)
    return render(request, 'travel/profile/profile.html', {'profile': profile})


#-------------------------------------------------------------------------------
def _add_todos(request):
    return render(request, 'travel/construction.html')


#-------------------------------------------------------------------------------
def todo_lists(request):
    if request.user.is_authenticated():
        todos = travel.ToDoList.objects.all_for_user(request.user)
    else:
        todos = travel.ToDoList.objects.filter(is_public=True)

    return render(request, 'travel/todo/listing.html', {'todos': todos})


#-------------------------------------------------------------------------------
def todo_list(request, pk):
    todo = get_object_or_404(travel.ToDoList, pk=pk)
    is_anon = request.user.is_anonymous()
    
    entities = []
    total = done = 0
    for entity in todo.entities.all():
        total += 1
        if is_anon:
            logged = 0
        else:
            logged = entity.travellog_set.filter(user=request.user).count()
            if logged:
                done += 1
    
        entities.append((entity, logged))
        
    data = {'todo': todo, 'entities': entities, 'stats': {'total': total, 'done': done}}
    return render(request, 'travel/todo/detail.html', data)


#-------------------------------------------------------------------------------
def search(request):
    search_form = forms.SearchForm(request.GET)
    data = {'search_form': search_form}
    if search_form.is_valid():
        q     = search_form.cleaned_data['search']
        mtype = search_form.cleaned_data['type']
        data.update(search=q, results=travel.Entity.objects.search(q, mtype))

    return render(request, 'travel/search/search.html', data)


#-------------------------------------------------------------------------------
@login_required
def search_advanced(request):
    # 'travel-search-advanced'
    data = {'results': None, 'search': ''}
    search = request.GET.get('search', '').strip()
    if search:
        lines = [line.strip() for line in search.splitlines()]
        data['search'] = '\n'.join(lines)
        q = models.Q()
        for term in lines:
            q |= (
                models.Q(name__icontains=term)      |
                models.Q(full_name__icontains=term) |
                models.Q(locality__icontains=term)  |
                models.Q(code__iexact=term)
            )
            
        data['results'] = travel.Entity.objects.filter(q)
        
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
@login_required
def entity_edit(request, ref, code, aux=None):
    if not request.user.is_superuser:
        return _handle_entity(request, ref, code, aux, _entity_base)
        
    return _handle_entity(request, ref, code, aux, _entity_edit)


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


#-------------------------------------------------------------------------------
def http_redirect_reverse(name, *args):
    return http.HttpResponseRedirect(reverse(name, args=args))


#-------------------------------------------------------------------------------
@utils.superuser_required
def start_add_entity(request):
    abbr = request.GET.get('type')
    if abbr:
        if abbr == 'co':
            return http_redirect_reverse('travel-entity-add-co')
            
        co = request.GET.get('country')
        if co:
            return http_redirect_reverse('travel-entity-add-by-co', co, abbr)
    
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


NEW_ENTITY_FORMS = {
    'st': forms.NewStateForm
}


#-------------------------------------------------------------------------------
@utils.superuser_required
def add_entity_by_co(request, code, abbr):
    entity_type = get_object_or_404(travel.EntityType, abbr=abbr)
    country = travel.Entity.objects.get(code=code, type__abbr='co')

    Form = NEW_ENTITY_FORMS[abbr]
    if request.method == 'POST':
        form = Form(request.POST)
        if form.is_valid():
            entity = form.save(entity_type, country=country)
            return http.HttpResponseRedirect(entity.get_absolute_url())
    else:
        form = Form()
    
    return render(
        request,
        'travel/entities/add/add.html',
        {'entity_type': entity_type, 'form': form}
    )
