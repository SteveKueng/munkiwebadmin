from django.conf.urls import patterns, include, url

urlpatterns = patterns('reports.views',
    url(r'^index/*$', 'index'),
    url(r'^dashboard/*$', 'dashboard'),
    url(r'^$', 'index'),
    url(r'^detail/(?P<serial>[^/]+)$', 'detail'),
    url(r'^detailpkg/(?P<manifest_name>[^/]+)/(?P<serial>[^/]+)$', 'detail_pkg'),
    url(r'^raw/(?P<serial>[^/]+)$', 'raw'),
    url(r'^submit/(?P<submission_type>[^/]+)$', 'submit'),
    url(r'^warranty/(?P<serial>[^/]+)$', 'warranty'),
   
    # for compatibilty with MunkiReport scripts
    url(r'^ip$', 'lookup_ip'),
    url(r'^(?P<submission_type>[^/]+)$', 'submit'),
)