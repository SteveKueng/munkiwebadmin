from django.conf.urls import patterns, include, url

urlpatterns = patterns('reports.views',
    url(r'^index/*$', 'index'),
    url(r'^dashboard/*$', 'dashboard'),
    url(r'^$', 'index'),
    url(r'^detail/(?P<serial>[^/]+)$', 'detail'),
    url(r'^detailpkg/(?P<serial>[^/]+)/(?P<manifest_name>[^/]+)$', 'detail_pkg'),
    url(r'^detailmachine/(?P<serial>[^/]+)$', 'machine_detail'),
    url(r'^appleupdate/(?P<serial>[^/]+)$', 'appleupdate'),
    url(r'^staging/(?P<serial>[^/]+)$', 'staging'),
    url(r'^raw/(?P<serial>[^/]+)$', 'raw'),
    url(r'^name/(?P<serial>[^/]+)$', 'getname'),
    url(r'^submit/(?P<submission_type>[^/]+)$', 'submit'),
    url(r'^warranty/(?P<serial>[^/]+)$', 'warranty'),
    url(r'^imagr/(?P<serial>[^/]+)$', 'imagr'),

    # for compatibilty with MunkiReport scripts
    url(r'^ip$', 'lookup_ip'),
    url(r'^(?P<submission_type>[^/]+)$', 'submit'),
)
