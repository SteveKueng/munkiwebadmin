# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from munkiwebadmin.django_basic_auth import logged_in_or_basicauth
import logging

LOGGER = logging.getLogger('munkiwebadmin')

@logged_in_or_basicauth()
def index(request):
    '''Index methods'''
    LOGGER.debug("Got index request for santa")
    context = {'page': 'santa'}
