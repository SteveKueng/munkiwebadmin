from django.urls import re_path as url
import inventory.views

urlpatterns = [
    url(r'^$', inventory.views.index, name='inventory'),
    url(r'^hash/(?P<serial>[^/]+)$', inventory.views.inventory_hash),
    url(r'^detail/(?P<serial>[^/]+)$', inventory.views.detail, name='inventory.detail'),
    url(r'^items/*$', inventory.views.items, name='inventory.items'),
    url(r'^items.json/*$', inventory.views.items_json),
]
    