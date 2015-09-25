from django.conf.urls import patterns, include, url

urlpatterns = patterns('pkgs.views',
	url(r'^index/*$', 'index'),
	url(r'^confirm/*$', 'confirm'),
	url(r'^done/*$', 'done'),
	url(r'^$', 'index'),
	#url(r'^(?P<pkgs_name>[^/]+)/(?P<item_name>[^/]+)/$', 'test_index'),
	#url(r'^(?P<pkgs_name>[^/]+)/edit/$', 'edit'),
)