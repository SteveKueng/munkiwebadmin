from django.urls import re_path as url
import manifests.views

urlpatterns = [
    url(r'^$', manifests.views.index, name='manifests'),
    url(r'^__get_manifest_list_status$', manifests.views.status),
    url(r'^(?P<manifest_path>.*$)', manifests.views.index)
]