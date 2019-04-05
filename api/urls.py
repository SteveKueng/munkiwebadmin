from django.conf.urls import url
import api.views

urlpatterns = [
    url(r'^(?P<kind>catalogs$)', api.views.plist_api),
    url(r'^(?P<kind>catalogs)/(?P<filepath>.*$)', api.views.plist_api),
    url(r'^(?P<kind>manifests$)', api.views.plist_api),
    url(r'^(?P<kind>manifests)/(?P<filepath>.*$)', api.views.plist_api),
    url(r'^(?P<kind>pkgsinfo$)', api.views.plist_api),
    url(r'^(?P<kind>pkgsinfo)/(?P<filepath>.*$)', api.views.plist_api),
    url(r'^(?P<kind>icons$)', api.views.file_api),
    url(r'^(?P<kind>icons)/(?P<filepath>.*$)', api.views.file_api),
    url(r'^(?P<kind>pkgs$)', api.views.file_api),
    url(r'^(?P<kind>pkgs)/(?P<filepath>.*$)', api.views.file_api),
    url(r'^(?P<kind>vault)/(?P<subclass>[a-zA-Z]+$)', api.views.db_api),
    url(r'^(?P<kind>vault)/(?P<subclass>[a-zA-Z]+)/(?P<serial_number>[a-zA-Z0-9]+$)', api.views.db_api),
    url(r'^(?P<kind>mdm)(?:/(?P<submission_type>.[a-zA-Z_]+))(?:/(?P<primary_id>[a-zA-Z0-9]+))(?:/(?P<action>[a-zA-Z_]+))(?:/(?P<secondary_id>[a-zA-Z0-9]+))?', api.views.mdm_api),
    url(r'^(?P<kind>mdm)(?:/(?P<submission_type>.[a-zA-Z_]+))(?:/(?P<primary_id>[a-zA-Z0-9]+))(?:/(?P<action>[a-zA-Z_]+))?', api.views.mdm_api),
    url(r'^(?P<kind>mdm)(?:/(?P<submission_type>.[a-zA-Z_]+))(?:/(?P<primary_id>[a-zA-Z0-9]+))?', api.views.mdm_api),
    url(r'^(?P<kind>mdm)(?:/(?P<submission_type>[a-zA-Z_]+))?', api.views.mdm_api),
    url(r'^(?P<kind>spectre)(?:/(?P<submission_type>.[a-zA-Z_]+))(?:/(?P<id>[a-zA-Z0-9-_]+))?', api.views.spectre_api),
    url(r'^(?P<kind>santa)(?:/(?P<submission_type>[a-zA-Z]+))(?:/(?P<machine_id>[a-zA-Z0-9]+))?', api.views.santa_api),
    url(r'^(?P<kind>inventory)/(?P<serial_number>[a-zA-Z0-9]+$)', api.views.db_api),
    url(r'^(?P<kind>[a-zA-Z]+$)', api.views.db_api),
    url(r'^(?P<kind>[a-zA-Z]+)/(?P<serial_number>.[a-zA-Z0-9]+$)', api.views.db_api),
]
