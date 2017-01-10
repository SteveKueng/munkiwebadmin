from django.conf.urls import url
import reports.views

urlpatterns = [
    url(r'^$', reports.views.index),

    url(r'^_catalogJson$', reports.views.createRequired),
    url(r'^_status$', reports.views.getStatus),
    url(r'^_getManifest/(?P<manifest_path>[^/]+)$', reports.views.getManifest),
    url(r'^(?P<computer_serial>[^/]+)$', reports.views.index),
    
    url(r'^dashboard/*$', reports.views.dashboard),
    url(r'^raw/(?P<serial>[^/]+)$', reports.views.raw),
    url(r'^warranty/(?P<serial>[^/]+)$', reports.views.warranty),
]
