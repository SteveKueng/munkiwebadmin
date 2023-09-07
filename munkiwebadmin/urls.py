from django.urls import re_path as url
from django.urls import include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from  django.contrib.auth.views import LoginView, logout_then_login
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

import os
try:
	BASE_DIR = settings.BASE_DIR
except:
	BASE_DIR = ""

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    url(r'^logout/', logout_then_login, name='logout'),
    url(r'^api/', include('api.urls')),
    url(r'^manifests/', include('manifests.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^catalogs/', include('catalogs.urls')),
    url(r'^pkgsinfo/', include('pkgsinfo.urls')),
    url(r'^icons/', include('icons.urls')),
    url(r'^inventory/', include('inventory.urls')),
    url(r'^santa/', include('santa.urls')),
    url(r'^makecatalogs/', include('process.urls')),
    url(r'^$', RedirectView.as_view(url='/reports/')),
]

# comment out the following if you are serving
# static files a different way
urlpatterns += staticfiles_urlpatterns()

# debug/development serving MEDIA files (icons)
try:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
except django.core.exceptions.ImproperlyConfigured:
    print("**** MEDIA_URL or MEDIA_ROOT missing from settings.py       ****")
    print("**** copy MEDIA_URL or MEDIA_ROOT from settings_template.py ****")
    raise
