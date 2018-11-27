# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import logging

LOGGER = logging.getLogger('munkiwebadmin')

@login_required
def index(request):
    '''Index methods'''
    LOGGER.debug("Got index request for santa")
    context = {'page': 'santa'}
