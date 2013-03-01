from django.conf.urls.defaults import *
from jargon.shortcuts import to_template
from travel import views


urlpatterns = patterns('',
    url(r'^$', to_template('travel/home.html'), name='travel-home'),
    url(r'^search/$', views.search, name='travel-search'),
    url(r'^i/(\w+)/$', views.by_locale, name='travel-by-locale'),
    url(r'^i/(\w+)/(\w+)/$', views.entity, name='travel-entity'),
    url(r'^i/(\w+)/(\w+)/(\w+)/$', views.entity_relationship, name='travel-entity-relationship'),

    url(r'^site/about/$', to_template('travel/site/about.html'), name='travel-about'),
    url(r'^site/request/$', views.support_request, kwargs={'title': 'Feature Request'}, name='travel-request'),
    url(r'^site/problem/$', views.support_request, kwargs={'title': 'Site Problem'}, name='travel-problem'),
    url(r'^site/thanks/$', to_template('travel/site/thank_you.html'), name='travel-thanks'),

    url(r'^flag/(\w+)/(\d+)/$', views.flag_upload, name='travel-flag-upload'),

    url(r'^profile/$', views.all_profiles, name='travel-profiles'),
    url(r'^profiles/([^/]+)/$', views.profile, name='travel-profile'),

    url(r'^todo/$', views.todo_lists, name='travel-todos'),
    url(r'^todo/(\d+)/$', views.todo_list, name='travel-todo'),

)
