from django.conf.urls import patterns, include, url

urlpatterns = patterns('packages.views',
	url(r'^index/*$', 'index'),
	url(r'^confirm/*$', 'confirm'),
	url(r'^done/*$', 'done'),
	url(r'^$', 'index'),
	#url(r'^(?P<packages_name>[^/]+)/(?P<item_name>[^/]+)/$', 'test_index'),
	#url(r'^(?P<packages_name>[^/]+)/edit/$', 'edit'),
)