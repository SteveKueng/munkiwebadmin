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
    url(r'^(?P<kind>[a-zA-Z]+$)', api.views.db_api),
    url(r'^(?P<kind>[a-zA-Z]+)/(?P<subclass>.*$)', api.views.db_api),
]
