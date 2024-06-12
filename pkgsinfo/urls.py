from django.urls import re_path as url
import pkgsinfo.views

urlpatterns = [
    url(r'^$', pkgsinfo.views.index, name='pkginfo'),
    url(r'^__get_process_status$', pkgsinfo.views.status),
    url(r'^_json$', pkgsinfo.views.getjson),
    url(r'^(?P<pkginfo_path>^.*$)', pkgsinfo.views.detail)
]