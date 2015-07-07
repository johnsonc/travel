from django.conf.urls import *
from django.views.generic import TemplateView, RedirectView
from travel import views, flag_game

search_patterns = [
    url(r'^$',          views.search, name='travel-search'),
    url(r'^advanced/$', views.search_advanced, name='travel-search-advanced'),
]

item_patterns = [
    url(r'^$',                                 views.by_locale, name='travel-by-locale'),
    url(r'^(?P<code>\w+)(?:-(?P<aux>\w+))?/$', views.entity, name='travel-entity'),
    url(r'^(?P<code>\w+)(?:-(?P<aux>\w+))?/(?P<rel>\w+)/$', views.entity_relationships, name='travel-entity-relationships'),
]

add_patterns = [
    url(r'^$',                views.start_add_entity, name='travel-entity-start-add'),
    url(r'^co/$',             views.add_entity_co, name='travel-entity-add-co'),
    url(r'^co/(\w+)/(\w+)/$', views.add_entity_by_co, name='travel-entity-add-by-co'),
]

profile_patterns = [
    url(r'^$',                   views.all_profiles, name='travel-profiles'),
    url(r'^([^/]+)/$',           views.profile, name='travel-profile'),
    url(r'^([^/]+)/log/(\d+)/$', views.log_entry, name='travel-log-entry'),
]

bucket_list_patterns = [
    url(r'^$',               views.bucket_lists, name='travel-buckets'),
    url(r'^(\d+)/$',         views.bucket_list, name='travel-bucket'),
    url(r'^(\d+)/([^/]+)/$', views.bucket_list_for_user, name='travel-bucket-for_user'),
    url(r'^(\d+)/(.+)/$',    views.bucket_list_comparison, name='travel-bucket-for_user'),
]

quiz_patterns = [
    url(r'^flags/$', flag_game.flag_game, name='travel-flag-quiz'),
]

urlpatterns = [
    url(r'^search/',          include(search_patterns)),
    url(r'^i/(?P<ref>\w+)/',  include(item_patterns)),
    url(r'^add/',             include(add_patterns)),
    url(r'^profiles/',        include(profile_patterns)),
    url(r'^buckets/',         include(bucket_list_patterns)),
    url(r'^quiz/',            include(quiz_patterns)),
    url(r'^edit/i/(\w+)/(\w+)(?:-(\w+))?/$', views.entity_edit, name='travel-entity-edit'),
    url(r'^plugs/$', TemplateView.as_view(template_name='travel/plugs.html'), name='travel-plugs'),
]
