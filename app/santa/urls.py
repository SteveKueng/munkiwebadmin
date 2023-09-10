from django.urls import re_path as url
import santa.views

urlpatterns = [
    url(r'^\Z', santa.views.index, name='santa'),
]