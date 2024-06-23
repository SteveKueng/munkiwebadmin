"""
process/views.py
"""

from django.http import HttpResponse
from process.models import Process
from django.views.decorators.csrf import csrf_exempt

import json
import logging
import os

from django.conf import settings
from api.models import MunkiRepo
from process.utils import record_status

REPO_DIR = settings.MUNKI_REPO_URL
MAKECATALOGS = settings.MAKECATALOGS_PATH

FLAG_FILE = '/tmp/makecatalogs_running'
MAKECATALOGS_STATUS_TAG = 'makecatalogs_process'

LOGGER = logging.getLogger('munkiwebadmin')

def index(request):
    '''Not implemented'''
    return HttpResponse(json.dumps('view not implemented'),
                        content_type='application/json')


def record(message=None, percent_done=None):
    '''Record a status message for a long-running process'''
    record_status(
        MAKECATALOGS_STATUS_TAG, message=message, percent_done=percent_done)


@csrf_exempt
def run(request):
    '''Start running our lengthy process'''
    if request.method == 'POST':
        LOGGER.debug('got run request for makecatalogs')
        
        try:
            MunkiRepo.makecatalogs(output_fn=record)
        except Exception as err:
            LOGGER.error('makecatalogs error: %s', err)
            
        return HttpResponse(json.dumps('done'),
                            content_type='application/json')
    return HttpResponse(json.dumps('must be a POST request'),
                        content_type='application/json')


def status(request):
    '''Get status of our lengthy process'''
    LOGGER.debug('got status request for makecatalogs')
    status_response = {}
    processes = Process.objects.filter(name=MAKECATALOGS_STATUS_TAG)
    if processes:
        # display status from one of the active processes
        # (hopefully there is only one!)
        process = processes[0]
        status_response['exited'] = False
        status_response['statustext'] = process.statustext
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