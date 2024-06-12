from django.urls import re_path as url
import icons.views

urlpatterns = [
    url(r'^$', icons.views.index, name='icons'),
    url(r'^__get_process_status$', icons.views.status),
]