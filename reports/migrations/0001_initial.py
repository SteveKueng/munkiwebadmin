# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-02-14 10:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessUnit',
            fields=[
                ('hash', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=30, unique=True)),
            ],
            options={
                'permissions': (('can_view_businessunit', 'Can view business unit'),),
            },
        ),
        migrations.CreateModel(
            name='ImagrReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=200)),
                ('message', models.CharField(max_length=512)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-date_added'],
                'get_latest_by': 'date_added',
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('serial_number', models.CharField(max_length=16, primary_key=True, serialize=False, unique=True)),
                ('hostname', models.CharField(max_length=64)),
                ('username', models.CharField(blank=True, default=b'unknown', max_length=256)),
                ('remote_ip', models.CharField(blank=True, max_length=15)),
                ('machine_model', models.CharField(blank=True, default=b'virtual-machine', max_length=64)),
                ('cpu_type', models.CharField(blank=True, max_length=64)),
                ('cpu_speed', models.CharField(blank=True, max_length=32)),
                ('cpu_arch', models.CharField(blank=True, max_length=32)),
                ('ram', models.CharField(blank=True, max_length=16)),
                ('os_version', models.CharField(blank=True, max_length=16)),
                ('imagr_workflow', models.CharField(blank=True, max_length=64)),
                ('current_imagr_status', models.CharField(blank=True, max_length=200)),
                ('businessunit', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='reports.BusinessUnit')),
            ],
            options={
                'ordering': ['hostname'],
            },
        ),
        migrations.CreateModel(
            name='MunkiReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('runtype', models.CharField(max_length=64)),
                ('runstate', models.CharField(max_length=16)),
                ('console_user', models.CharField(max_length=64)),
                ('errors', models.IntegerField(default=0)),
                ('warnings', models.IntegerField(default=0)),
                ('activity', models.TextField(editable=False, null=True)),
                ('report', models.TextField(editable=False, null=True)),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.Machine')),
            ],
            options={
                'ordering': ['machine'],
                'permissions': (('can_view_reports', 'Can view reports'), ('can_view_dashboard', 'Can view dashboard')),
            },
        ),
        migrations.AddField(
            model_name='imagrreport',
            name='machine',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.Machine'),
        ),
    ]
