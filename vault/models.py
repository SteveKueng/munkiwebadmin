from __future__ import unicode_literals

import django
from django.db import models
from django.contrib.auth.models import User
from encrypted_fields import EncryptedCharField, EncryptedDateTimeField
from datetime import timedelta

from reports.models import Machine

class passwordAccess(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, editable=False)
    user = models.ForeignKey(User, editable=False)
    reason = models.CharField(max_length=140, editable=False)
    date = models.DateTimeField(default=django.utils.timezone.now, editable=False)

    class Meta:
        permissions = (
            ('view_passwordAccess', 'View content'),
        )

class localAdmin(models.Model):
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE, primary_key=True, editable=False)
    password = EncryptedCharField(editable=False, max_length=12)
    expireDate = EncryptedDateTimeField(editable=False)

    def getPassword(self, user, reason):
        self.expireDate = django.utils.timezone.now() + timedelta(hours=2)
        access = passwordAccess(machine=self.machine, user=user, reason=reason)
        access.save()
        self.save()
        return self.password

    def setPassword(self, value):
        self.expireDate = django.utils.timezone.now() + timedelta(days=1)
        self.password = value
    
    class Meta:
        permissions = (
            ('show_password', 'Show password'),
            ('view_expireDate', 'view expire date'),
        )