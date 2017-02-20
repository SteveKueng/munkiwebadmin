from django.conf.urls import url
import api.views

urlpatterns = [
    url(r'^(?P<kind>manifests$)', api.views.plist_api),
    url(r'^(?P<kind>manifests)/(?P<filepath>.*$)', api.views.plist_api),
    url(r'^(?P<kind>pkgsinfo$)', api.views.plist_api),
    url(r'^(?P<kind>pkgsinfo)/(?P<filepath>.*$)', api.views.plist_api),
    url(r'^(?P<kind>icons$)', api.views.file_api),
    url(r'^(?P<kind>icons)/(?P<filepath>.*$)', api.views.file_api),
    url(r'^(?P<kind>pkgs$)', api.views.file_api),
    url(r'^(?P<kind>pkgs)/(?P<filepath>.*$)', api.views.file_api),
    url(r'^(?P<kind>report$)', api.views.db_api),
    url(r'^(?P<kind>report)/(?P<serial_number>.*$)', api.views.db_api),
    url(r'^(?P<kind>imagr$)', api.views.db_api),
    url(r'^(?P<kind>imagr)/(?P<serial_number>.*$)', api.views.db_api),
]
