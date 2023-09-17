from django.db import models
from reports.models import Machine

class Inventory(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    datestamp = models.DateTimeField(auto_now=True)
    sha256hash = models.CharField(max_length=64)
    class Meta:
        ordering = ['datestamp']
        permissions = (("can_view_inventory", "Can view inventory"),)


class InventoryItem(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    version = models.CharField(max_length=32)
    bundleid = models.CharField(max_length=256)
    bundlename = models.CharField(max_length=256)
    path = models.CharField(max_length=1024)
    class Meta:
        ordering = ['name', '-version']