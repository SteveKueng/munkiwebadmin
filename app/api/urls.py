from django.urls import re_path as url
from api.views import ReportsListAPIView, ReportsDetailAPIView, CatalogsListView, CatalogsDetailAPIView, ManifestsListView, ManifestsDetailAPIView, PkgsinfoListView, PkgsinfoDetailAPIView, PkgsListView, PkgsDetailAPIView, IconsListView, IconsDetailAPIView

urlpatterns = [
    url(r'^reports/?$', ReportsListAPIView.as_view(), name="report-list"),
    url(r'^reports/(?P<serial_number>[a-zA-Z0-9]+)$', ReportsDetailAPIView.as_view(), name="report-detail"),
    url(r'^catalogs/?$', CatalogsListView.as_view(), name="catalog-list"),
    url(r'^catalogs/(?P<filepath>.*$)', CatalogsDetailAPIView.as_view(), name="catalog-detail"),
    url(r'^manifests/?$', ManifestsListView.as_view(), name="manifest-list"),
    url(r'^manifests/(?P<filepath>.*$)', ManifestsDetailAPIView.as_view()),
    url(r'^pkgsinfo/?$', PkgsinfoListView.as_view(), name="pkgsinfo-list"),
    url(r'^pkgsinfo/(?P<filepath>.*$)', PkgsinfoDetailAPIView.as_view(), name="pkgsinfo-detail"),
    url(r'^pkgs/?$', PkgsListView.as_view(), name="pkgs-list"),
    url(r'^pkgs/(?P<filepath>.*$)', PkgsDetailAPIView.as_view(), name="pkgs-download"),
    url(r'^icons/?$', IconsListView.as_view(), name="icon-list"),
    url(r'^icons/(?P<filepath>.*$)', IconsDetailAPIView.as_view(), name="icon-download"),
]