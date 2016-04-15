from django.conf.urls import url
import reports.views

urlpatterns = [
    url(r'^$', reports.views.index),
    url(r'^dashboard/*$', reports.views.dashboard),

    url(r'^delete/(?P<serial>[^/]+)$', reports.views.delete_machine),
    url(r'^detail/(?P<serial>[^/]+)$', reports.views.detail),
    url(r'^detailpkg/(?P<serial>[^/]+)/(?P<manifest_name>[^/]+)$', reports.views.detail_pkg),
    url(r'^detailmachine/(?P<serial>[^/]+)$', reports.views.machine_detail),
    url(r'^appleupdate/(?P<serial>[^/]+)$', reports.views.appleupdate),
    url(r'^staging/(?P<serial>[^/]+)$', reports.views.staging),
    url(r'^raw/(?P<serial>[^/]+)$', reports.views.raw),
    url(r'^name/(?P<serial>[^/]+)$', reports.views.getname),
    url(r'^submit/(?P<submission_type>[^/]+)$', reports.views.submit),
    url(r'^warranty/(?P<serial>[^/]+)$', reports.views.warranty),
    url(r'^imagr/(?P<serial>[^/]+)$', reports.views.imagr),

    # for compatibilty with MunkiReport scripts
    url(r'^ip$', reports.views.lookup_ip),
    url(r'^(?P<submission_type>[^/]+)$', reports.views.submit),
]
