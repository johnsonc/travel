from django.conf.urls import *
from travel import views


urlpatterns = patterns('',
    url(r'^$', views.home, name='travel-home'),
    url(r'^about/$', view.to_template('travel/about.html'), name='travel-about'),
    url(r'^search/$', views.search, name='travel-search'),
    url(r'^search/advanced/$', views.search_advanced, name='travel-search-advanced'),

    url(r'^i/(\w+)/$', views.by_locale, name='travel-by-locale'),
    url(r'^i/(\w+)/(\w+)(?:-(\w+))?/$', views.entity, name='travel-entity'),
    url(r'^i/(\w+)/(\w+)/(\w+)/$', views.entity_relationships, name='travel-entity-relationships'),
    url(r'^i/(\w+)/(\w+)/(\w+)/(\w+)/$', views.entity_by_parent, name='travel-entity-by-parent'),

    url(r'^add/$', views.start_add_entity, name='travel-entity-start-add'),
    url(r'^add/co/$', views.add_entity_co, name='travel-entity-add-co'),
    url(r'^add/co/(\w+)/(\w+)/$', views.add_entity_by_co, name='travel-entity-add-by-co'),
    url(r'^fix/$', views.fix_shit, name='travel-fix'),
    
    url(r'^edit/i/(\w+)/(\w+)(?:-(\w+))?/$', views.entity_edit, name='travel-entity-edit'),
    url(r'^site/request/$', views.support_request, kwargs={'title': 'Feature Request'}, name='travel-request'),
    url(r'^site/problem/$', views.support_request, kwargs={'title': 'Site Problem'}, name='travel-problem'),
    url(r'^site/thanks/$', view.to_template('travel/site/thank_you.html'), name='travel-thanks'),

    url(r'^profile/$', views.all_profiles, name='travel-profiles'),
    url(r'^profiles/([^/]+)/$', views.profile, name='travel-profile'),
    url(r'^profiles/([^/]+)/log/(\d+)/$', views.log_entry, name='travel-log-entry'),

    url(r'^todo/$', views.todo_lists, name='travel-todos'),
    url(r'^todo/(\d+)/$', views.todo_list, name='travel-todo'),

    url(r'^plugs/$', view.to_template('travel/plugs.html'), name='travel-plugs'),
)
