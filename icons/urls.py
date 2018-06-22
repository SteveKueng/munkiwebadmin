from django.conf.urls import url
import icons.views

urlpatterns = [
    url(r'^$', icons.views.index, name='icons'),
    url(r'^__get_process_status$', icons.views.status),
]