"""
manifests/models.py
"""
from django.db import models

class ManifestFile(models.Model):
    '''Placeholder so we get permissions entries in the admin database'''
    class Meta:
        permissions = (
            ('view', 'View manifest'),
        )
    pass
