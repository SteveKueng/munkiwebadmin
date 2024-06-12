# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import logging
import json
from django.http import HttpResponse
from process.models import Process

from pkgsinfo.models import PKGSINFO_STATUS_TAG

LOGGER = logging.getLogger('munkiwebadmin')

@login_required
def index(request):
    '''Index methods'''
    LOGGER.debug("Got index request for icons")
    context = {'page': 'icons'}
    return render(request, 'icons/icons.html', context=context)

def status(request):
    '''Get and return a status message for the process generating
    the pkgsinfo list'''
    LOGGER.debug('got status request for pkgsinfo_list_process')
    status_response = {}
    processes = Process.objects.filter(name=PKGSINFO_STATUS_TAG)
    if processes:
        # display status from one of the active processes
        # (hopefully there is only one!)
        process = processes[0]
        status_response['statustext'] = process.statustext
    else:
        status_response['statustext'] = 'Processing'
    return HttpResponse(json.dumps(status_response),
                        content_type='application/json')