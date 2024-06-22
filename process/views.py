"""
process/views.py
"""

from django.http import HttpResponse
from process.models import Process
from django.views.decorators.csrf import csrf_exempt

import json
import logging
import os
import subprocess
import time
import sys

from django.conf import settings
from api.models import MunkiRepo

REPO_DIR = settings.MUNKI_REPO_URL
MAKECATALOGS = settings.MAKECATALOGS_PATH

FLAG_FILE = '/tmp/makecatalogs_running'
STATUS_TEXT = ''

LOGGER = logging.getLogger('munkiwebadmin')

def index(request):
    '''Not implemented'''
    return HttpResponse(json.dumps('view not implemented'),
                        content_type='application/json')

def update_status(status):
    '''Update the status of our process'''
    LOGGER.debug('update_status: %s', status)
    STATUS_TEXT = status

@csrf_exempt
def run(request):
    '''Start running our lengthy process'''
    if request.method == 'POST':
        LOGGER.debug('got run request for makecatalogs')

        # create flag file to indicate that makecatalogs is running
        if os.path.exists(FLAG_FILE):
            return HttpResponse(json.dumps('makecatalogs already running'),
                                content_type='application/json')
        open(FLAG_FILE, 'w').close()
        
        try:
            MunkiRepo.makecatalogs(output_fn=update_status)
        except Exception as err:
            LOGGER.error('makecatalogs error: %s', err)
        finally:
            try:
                STATUS_TEXT = ''
                os.unlink(FLAG_FILE)
            except OSError:
                pass
        return HttpResponse(json.dumps('done'),
                            content_type='application/json')
    return HttpResponse(json.dumps('must be a POST request'),
                        content_type='application/json')


def status(request):
    '''Get status of our lengthy process'''
    LOGGER.debug('got status request for makecatalogs')
    status_response = {}
    
    if os.path.exists(FLAG_FILE):
        # display status from one of the active processes
        # (hopefully there is only one!)
        status_response['exited'] = False
        status_response['statustext'] = STATUS_TEXT
        status_response['exitcode'] = 0
    else:
        status_response['exited'] = True
        status_response['statustext'] = 'no such process'
        status_response['exitcode'] = -1
    return HttpResponse(json.dumps(status_response),
                        content_type='application/json')


def delete(request):
    '''Remove record for our process'''
    LOGGER.debug('got delete request for makecatalogs')
    try:
        os.unlink(FLAG_FILE)
    except Process.DoesNotExist:
        pass
    return HttpResponse(json.dumps('done'),
                        content_type='application/json')