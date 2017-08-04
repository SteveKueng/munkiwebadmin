from django.db import models

class Updates(models.Model):
    '''Placeholder so we get permissions entries in the admin database'''
    class Meta:
        permissions = (
            ('view', 'View updates'),
        )
    pass
