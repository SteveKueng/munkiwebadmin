# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-02-15 11:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='machine',
            old_name='current_imagr_status',
            new_name='current_status',
        ),
    ]
