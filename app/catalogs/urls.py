from django.urls import re_path as url
import catalogs.views

urlpatterns = [
    url(r'^$', catalogs.views.catalog_view, name='catalogs'),
    url(r'^_json_catalog_data_$', catalogs.views.json_catalog_data),
    url(r'^get_pkg_ref_count/(?P<pkg_path>.*$)', catalogs.views.get_pkg_ref_count)
]