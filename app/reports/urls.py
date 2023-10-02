from django.urls import re_path as url
import reports.views

urlpatterns = [
    url(r'^$', reports.views.index, name='reports'),
    url(r'^dashboard', reports.views.dashboard, name='dashboard'),

    url(r'^_catalogJson$', reports.views.createRequired),
    url(r'^_status$', reports.views.getStatus),
    url(r'^_json$', reports.views.getjson),
    url(r'^_getManifest/(?P<manifest_path>[^/]+)$', reports.views.getManifest),
    url(r'^downloadMunkiScripts$', reports.views.downloadMunkiScripts),
    url(r'^(?P<computer_serial>[^/]+)$', reports.views.index),
    
    url(r'^raw/(?P<serial>[^/]+)$', reports.views.raw),
    #url(r'^model/(?P<serial>[^/]+)$', reports.views.model_description_lookup),
    
]
