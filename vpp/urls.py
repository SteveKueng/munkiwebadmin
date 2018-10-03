from django.conf.urls import url
import vpp.views

urlpatterns = [
    url(r'^$', vpp.views.index, name='vpp'),
]
