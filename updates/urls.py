from django.conf.urls import url
import updates.views

urlpatterns = [
    url(r'^$', updates.views.index),
    url(r'^update_list$', updates.views.update_list),
    url(r'^process_queue$', updates.views.process_queue),
    url(r'^add_all/(?P<branchname>^.*$)', updates.views.add_all),
    url(r'^dup/(?P<frombranch>^)/(?P<tobranch>^.*$)', updates.views.dup),
    url(r'^delete_branch/(?P<branchname>^.*$)', updates.views.delete_branch),
    url(r'^new_branch/(?P<branchname>^.*$)', updates.views.new_branch),
    url(r'^delete_depr$', updates.views.purge_product),
    url(r'^__get_update_list_status$', updates.views.status),
]