from django.conf.urls import url
import santa.views

urlpatterns = [
    url(r'^\Z', santa.views.index, name='santa'),
]