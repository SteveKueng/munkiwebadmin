from django.conf.urls import url
import updates.views

urlpatterns = [
    url(r'^add_product$', updates.views.add_product_to_branch),
    url(r'^remove_product$', updates.views.remove_product_from_branch),
    url(r'^delete_branch/(?P<branchname>.*$)', updates.views.delete_branch),
    url(r'^new_branch/(?P<branchname>.*$)', updates.views.new_branch),
    url(r'^__get_update_list_status$', updates.views.status),
    url(r'^$', updates.views.index, name='updates'),
]