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
from munkiwebadmin.utils import MunkiGit

REPO_DIR = settings.MUNKI_REPO_DIR
MAKECATALOGS = settings.MAKECATALOGS_PATH

LOGGER = logging.getLogger('munkiwebadmin')

try:
    GIT = settings.GIT_PATH
except AttributeError:
    GIT = None

def pid_exists(pid):
    """Check whether pid exists in the current process table."""
    # http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
    if os.name == 'posix':
        # OS X and Linux
        import errno
        if pid < 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError as e:
            return e.errno == errno.EPERM
        else:
            return True
    else:
        # Windows
        import ctypes
        kernel32 = ctypes.windll.kernel32
        HANDLE = ctypes.c_void_p
        DWORD = ctypes.c_ulong
        LPDWORD = ctypes.POINTER(DWORD)
        class ExitCodeProcess(ctypes.Structure):
            _fields_ = [('hProcess', HANDLE),
                        ('lpExitCode', LPDWORD)]

        SYNCHRONIZE = 0x100000
        process = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
        if not process:
            return False

        ec = ExitCodeProcess()
        out = kernel32.GetExitCodeProcess(process, ctypes.byref(ec))
        if not out:
            err = kernel32.GetLastError()
            if kernel32.GetLastError() == 5:
                # Access is denied.
                logging.warning("Access is denied to get pid info.")
            kernel32.CloseHandle(process)
            return False
        elif bool(ec.lpExitCode):
            # print ec.lpExitCode.contents
            # There is an exist code, it quit
            kernel32.CloseHandle(process)
            return False
        # No exit code, it's running.
        kernel32.CloseHandle(process)
        return True

def index(request):
    '''Not implemented'''
    return HttpResponse(json.dumps('view not implemented'),
                        content_type='application/json')

@csrf_exempt
def run(request):
    '''Start running our lengthy process'''
    if request.method == 'POST':
        LOGGER.debug('got run request for makecatalogs')
        # remove records for exited processes
        Process.objects.filter(name='makecatalogs', exited=True).delete()
        while True:
            # Loop until there are no more running processes
            processes = Process.objects.filter(name='makecatalogs',
                                               exited=False)
            if not processes:
                break
            # clean up any processes no longer in the process table
            for process in processes:
                if not pid_exists(process.pid):
                    process.delete()
            processes = Process.objects.filter(name='makecatalogs',
                                               exited=False)
            if not processes:
                break
            # if we get here, there are still running processes
            LOGGER.debug('waiting for running makecatalogs processes to finish')
            time.sleep(1)

        LOGGER.debug('starting makecatalogs')
        proc = subprocess.Popen([sys.executable, MAKECATALOGS, REPO_DIR],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        record = Process(name='makecatalogs')
        record.pid = proc.pid
        record.save()
        while True:
            output = proc.stdout.readline().decode('utf-8').rstrip('\n')
            if output:
                record.statustext = output.rstrip('\n')
                record.save()
            if proc.poll() != None:
                break

        if request.user and GIT:
            MunkiGit().add_file_at_path(os.path.join(REPO_DIR, "icons"), request.user)
            MunkiGit().add_file_at_path(os.path.join(REPO_DIR, "catalogs"), request.user)
        record.statustext = 'Done'
        record.exited = True
        record.exitcode = proc.returncode
        record.save()
        return HttpResponse(json.dumps('done'),
                            content_type='application/json')
    return HttpResponse(json.dumps('must be a POST request'),
                        content_type='application/json')


def status(request):
    '''Get status of our lengthy process'''
    LOGGER.debug('got status request for makecatalogs')
    status_response = {}
    processes = Process.objects.filter(name='makecatalogs', exited=False)
    if processes:
        # display status from one of the active processes
        # (hopefully there is only one!)
        process = processes[0]
        status_response['exited'] = process.exited
        status_response['statustext'] = process.statustext
        status_response['exitcode'] = process.exitcode
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
        record = Process.objects.get(name='makecatalogs')
        record.delete()
    except Process.DoesNotExist:
        pass
    return HttpResponse(json.dumps('done'),
                        content_type='application/json')