from django.conf.urls import *
from django.views.generic import TemplateView
from travel import views

urlpatterns = patterns('',
    url(r'^search/$', views.search, name='travel-search'),
    url(r'^search/advanced/$', views.search_advanced, name='travel-search-advanced'),

    url(r'^i/(\w+)/$', views.by_locale, name='travel-by-locale'),
    url(r'^i/(\w+)/(\w+)(?:-(\w+))?/$', views.entity, name='travel-entity'),
    url(r'^i/(\w+)/(\w+)/(\w+)/$', views.entity_relationships, name='travel-entity-relationships'),

    url(r'^add/$', views.start_add_entity, name='travel-entity-start-add'),
    url(r'^add/co/$', views.add_entity_co, name='travel-entity-add-co'),
    url(r'^add/co/(\w+)/(\w+)/$', views.add_entity_by_co, name='travel-entity-add-by-co'),
    
    url(r'^edit/i/(\w+)/(\w+)(?:-(\w+))?/$', views.entity_edit, name='travel-entity-edit'),

    url(r'^profile/$', views.all_profiles, name='travel-profiles'),
    url(r'^profiles/([^/]+)/$', views.profile, name='travel-profile'),
    url(r'^profiles/([^/]+)/log/(\d+)/$', views.log_entry, name='travel-log-entry'),

    url(r'^todo/$', views.todo_lists, name='travel-todos'),
    url(r'^todo/(\d+)/$', views.todo_list, name='travel-todo'),

    url(r'^plugs/$', TemplateView.as_view(template_name='travel/plugs.html'), name='travel-plugs'),
    
)
