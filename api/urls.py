from django.conf.urls import url
from api.views import *

urlpatterns = [
    url(r'^reports$', ReportsListAPIView.as_view(), name="report-list"),
    url(r'^reports/(?P<serial_number>[a-zA-Z0-9]+)$', ReportsDetailAPIView.as_view(), name="report-detail"),
    url(r'^(?P<kind>catalogs$)', plist_api),
    url(r'^(?P<kind>catalogs)/(?P<filepath>.*$)', plist_api),
    url(r'^(?P<kind>manifests$)', plist_api),
    url(r'^(?P<kind>manifests)/(?P<filepath>.*$)', plist_api),
    url(r'^(?P<kind>pkgsinfo$)', plist_api),
    url(r'^(?P<kind>pkgsinfo)/(?P<filepath>.*$)', plist_api),
    url(r'^(?P<kind>icons$)', file_api),
    url(r'^(?P<kind>icons)/(?P<filepath>.*$)', file_api),
    url(r'^(?P<kind>pkgs$)', file_api),
    url(r'^(?P<kind>pkgs)/(?P<filepath>.*$)', file_api),
    url(r'^(?P<kind>vault)/(?P<subclass>[a-zA-Z]+$)', db_api),
    url(r'^(?P<kind>vault)/(?P<subclass>[a-zA-Z]+)/(?P<serial_number>[a-zA-Z0-9]+)', db_api),
    url(r'^(?P<kind>[a-zA-Z]+$)', db_api),
    url(r'^(?P<kind>[a-zA-Z]+)/(?P<serial_number>.[a-zA-Z0-9]+$)', db_api),
]
