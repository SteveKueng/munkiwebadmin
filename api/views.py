"""
api/views.py
"""
from django.http import HttpResponse
from django.http import QueryDict
from django.http import FileResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from api.models import Plist, MunkiFile
from api.models import FileError, FileWriteError, \
                       FileAlreadyExistsError, \
                       FileDoesNotExistError, FileDeleteError

from reports.models import Machine, MunkiReport, ImagrReport
from munkiwebadmin.django_basic_auth import logged_in_or_basicauth

import datetime
import json
import logging
import os
import mimetypes
import plistlib
import re

LOGGER = logging.getLogger('munkiwebadmin')

def normalize_value_for_filtering(value):
    '''Converts value to a list of strings'''
    if isinstance(value, (int, float, bool, basestring, dict)):
        return [str(value).lower()]
    if isinstance(value, list):
        return [str(item).lower() for item in value]
    return []


def convert_dates_to_strings(plist):
    '''Converts all date objects in a plist to strings. Enables encoding into
    JSON'''
    if isinstance(plist, dict):
        for key, value in plist.items():
            if isinstance(value, datetime.datetime):
                plist[key] = value.isoformat()
            if isinstance(value, (list, dict)):
                plist[key] = convert_dates_to_strings(value)
        return plist
    if isinstance(plist, list):
        for value in plist:
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            if isinstance(value, (list, dict)):
                value = convert_dates_to_strings(value)
        return plist


def convert_strings_to_dates(jdata):
    '''Attempt to automatically convert JSON date strings to date objects for
    plists'''
    iso_date_pattern = re.compile(
        r"^\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\dZ*$")
    if isinstance(jdata, dict):
        for key, value in jdata.items():
            if ('date' in key.lower() and isinstance(value, basestring)
                    and iso_date_pattern.match(value)):
                jdata[key] = datetime.datetime.strptime(
                    value[:19], "%Y-%m-%dT%H:%M:%S")
            if isinstance(value, (list, dict)):
                jdata[key] = convert_strings_to_dates(value)
        return jdata
    if isinstance(jdata, list):
        for value in jdata:
            # we don't support lists of dates, so no need to check
            # for those
            if isinstance(value, (list, dict)):
                value = convert_strings_to_dates(value)
        return jdata


@csrf_exempt
@logged_in_or_basicauth()
def plist_api(request, kind, filepath=None):
    '''Basic API calls for working with Munki plist files'''
    if kind not in ['manifests', 'pkgsinfo', 'catalogs']:
        return HttpResponse(status=404)

    response_type = 'json'
    if request.META.get('HTTP_ACCEPT') == 'application/xml':
        response_type = 'xml_plist'
    request_type = 'json'
    if request.META.get('CONTENT_TYPE') == 'application/xml':
        request_type = 'xml_plist'

    if request.method == 'GET':
        LOGGER.debug("Got API GET request for %s", kind)
        if filepath:
            response = Plist.read(kind, filepath)
            if response_type == 'json':
                response = convert_dates_to_strings(response)
        else:
            filter_terms = request.GET.copy()
            if '_' in filter_terms.keys():
                del filter_terms['_']
            if 'api_fields' in filter_terms.keys():
                api_fields = filter_terms['api_fields'].split(',')
                del filter_terms['api_fields']
            else:
                api_fields = None
            item_list = Plist.list(kind)
            response = []
            for item_name in item_list:
                if (api_fields == ['filename']
                        and filter_terms.keys() in ([], ['filename'])):
                    # don't read each manifest if all we want is filenames
                    plist = {'filename': item_name}
                    if 'filename' in filter_terms.keys():
                        if filter_terms['filename'].lower() not in item_name:
                            continue
                    response.append(plist)
                else:
                    plist = Plist.read(kind, item_name)
                    plist = convert_dates_to_strings(plist)
                    plist['filename'] = item_name
                    matches_filters = True
                    for key, value in filter_terms.items():
                        if key not in plist:
                            matches_filters = False
                            continue
                        plist_value = normalize_value_for_filtering(plist[key])
                        match = next(
                            (item for item in plist_value
                             if value.lower() in item.lower()), None)
                        if not match:
                            matches_filters = False
                            continue
                    if matches_filters:
                        if api_fields:
                            # filter to just the requested fields
                            plist = {key: plist[key] for key in plist.keys()
                                     if key in api_fields}
                        response.append(plist)
        if response_type == 'json':
            return HttpResponse(json.dumps(response) + '\n',
                                content_type='application/json')
        else:
            return HttpResponse(plistlib.writePlistToString(response),
                                content_type='application/xml')

    if request.META.has_key('HTTP_X_METHODOVERRIDE'):
        # support browsers/libs that don't directly support the other verbs
        http_method = request.META['HTTP_X_METHODOVERRIDE']
        if http_method.lower() == 'put':
            request.method = 'PUT'
            request.META['REQUEST_METHOD'] = 'PUT'
            request.PUT = QueryDict(request.body)
        if http_method.lower() == 'delete':
            request.method = 'DELETE'
            request.META['REQUEST_METHOD'] = 'DELETE'
            request.DELETE = QueryDict(request.body)
        if http_method.lower() == 'patch':
            request.method = 'PATCH'
            request.META['REQUEST_METHOD'] = 'PATCH'
            request.PATCH = QueryDict(request.body)

    if request.method == 'POST':
        LOGGER.debug("Got API POST request for %s", kind)
        if kind == 'manifests':
            if not request.user.has_perm('manifests.change_manifestfile'):
                raise PermissionDenied
        if kind == 'pkgsinfo':
            if not request.user.has_perm('pkgsinfo.change_pkginfofile'):
                raise PermissionDenied
        request_data = {}
        if request.body:
            if request_type == 'json':
                request_data = json.loads(request.body)
                request_data = convert_strings_to_dates(request_data)
            else:
                request_data = plistlib.readPlistFromString(request.body)
        if (filepath and 'filename' in request_data
                and filepath != request_data['filename']):
            return HttpResponse(
                json.dumps({
                    'result': 'failed',
                    'exception_type': 'AmbiguousResourceName',
                    'detail':
                    'File name was specified in both URI and content data'}),
                content_type='application/json', status=400)
        if filepath is None and 'filename' not in request_data:
            return HttpResponse(
                json.dumps({
                    'result': 'failed',
                    'exception_type': 'NoResourceName',
                    'detail':
                    'File name was not specified in URI or content data'}),
                content_type='application/json', status=400)
        if 'filename' in request_data:
            filepath = request_data['filename']
            del request_data['filename']
        try:
            Plist.new(kind, filepath, request.user, plist_data=request_data)
        except FileAlreadyExistsError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json',
                status=409)
        except FileWriteError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        except FileError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        else:
            if response_type == 'json':
                request_data = convert_dates_to_strings(request_data)
                return HttpResponse(
                    json.dumps(request_data) + '\n',
                    content_type='application/json', status=201)
            else:
                return HttpResponse(
                    plistlib.writePlistToString(request_data),
                    content_type='application/xml', status=201)

    elif request.method == 'PUT':
        LOGGER.debug("Got API PUT request for %s", kind)
        if kind == 'manifests':
            if not request.user.has_perm('manifests.change_manifestfile'):
                raise PermissionDenied
        if kind == 'pkgsinfo':
            if not request.user.has_perm('pkgsinfo.change_pkginfofile'):
                raise PermissionDenied
        if not filepath:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'WrongHTTPMethodType',
                            'detail': 'Perhaps this should be a POST request'}
                          ),
                content_type='application/json', status=400)
        if request_type == 'json':
            request_data = json.loads(request.body)
            request_data = convert_strings_to_dates(request_data)
        else:
            request_data = plistlib.readPlistFromString(request.body)
        if not request_data:
            # need to deal with this issue
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'NoRequestBody',
                            'detail':
                                'Request body was empty or missing valid data'}
                          ),
                content_type='application/json', status=400)
        if 'filename' in request_data:
            # perhaps support rename here in the future, but for now,
            # ignore it
            del request_data['filename']

        try:
            data = plistlib.writePlistToString(request_data)
            Plist.write(data, kind, filepath, request.user)
        except FileError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        else:
            if response_type == 'json':
                request_data = convert_dates_to_strings(request_data)
                return HttpResponse(
                    json.dumps(request_data) + '\n',
                    content_type='application/json')
            else:
                return HttpResponse(
                    plistlib.writePlistToString(request_data),
                    content_type='application/xml')

    elif request.method == 'PATCH':
        LOGGER.debug("Got API PATCH request for %s", kind)
        if kind == 'manifests':
            if not request.user.has_perm('manifests.change_manifestfile'):
                raise PermissionDenied
        if kind == 'pkgsinfo':
            if not request.user.has_perm('pkgsinfo.change_pkginfofile'):
                raise PermissionDenied
        if not filepath:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'WrongHTTPMethodType',
                            'detail': 'Perhaps this should be a POST request'}
                          ),
                content_type='application/json', status=400)
        if request_type == 'json':
            request_data = json.loads(request.body)
            request_data = convert_strings_to_dates(request_data)
        else:
            request_data = plistlib.readPlistFromString(request.body)
        if not request_data:
            # need to deal with this issue
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'NoRequestBody',
                            'detail':
                                'Request body was empty or missing valid data'}
                          ),
                content_type='application/json', status=400)
        if 'filename' in request_data:
            # perhaps support rename here in the future, but for now,
            # ignore it
            del request_data['filename']
        # read existing manifest
        plist_data = Plist.read(kind, filepath)
        #plist_data['filename'] = filepath
        plist_data.update(request_data)
        try:
            data = plistlib.writePlistToString(plist_data)
            Plist.write(data, kind, filepath, request.user)
        except FileError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        else:
            if response_type == 'json':
                plist_data = convert_dates_to_strings(plist_data)
                return HttpResponse(
                    json.dumps(plist_data) + '\n',
                    content_type='application/json')
            else:
                return HttpResponse(
                    plistlib.writePlistToString(plist_data),
                    content_type='application/xml')

    elif request.method == 'DELETE':
        LOGGER.debug("Got API DELETE request for %s", kind)
        if kind == 'manifests':
            if not request.user.has_perm('manifests.delete_manifestfile'):
                raise PermissionDenied
        if kind == 'pkgsinfo':
            if not request.user.has_perm('pkgsinfo.delete_pkginfofile'):
                raise PermissionDenied
        if not filepath:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'MassDeleteNotSupported',
                            'detail': 'Deleting all items is not supported'}
                          ),
                content_type='application/json', status=403)
        try:
            Plist.delete(kind, filepath, request.user)
        except FileDoesNotExistError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=404)
        except FileDeleteError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        except FileError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        else:
            # success
            return HttpResponse(status=204)


@csrf_exempt
@logged_in_or_basicauth()
def file_api(request, kind, filepath=None):
    '''Basic API calls for working with non-plist Munki files'''
    if kind not in ['icons', 'pkgs']:
        return HttpResponse(status=404)
    if request.method == 'GET':
        LOGGER.debug("Got API GET request for %s", kind)
        if filepath:
            fullpath = MunkiFile.get_fullpath(kind, filepath)
            if not os.path.exists(fullpath):
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': 'FileDoesNotExist',
                                'detail': '%s does not exist' % filepath}),
                    content_type='application/json', status=404)
            try:
                response = FileResponse(
                    open(fullpath, 'rb'),
                    content_type=mimetypes.guess_type(fullpath)[0])
                response['Content-Length'] = os.path.getsize(fullpath)
                response['Content-Disposition'] = (
                    'attachment; filename="%s"' % os.path.basename(filepath))
                return response
            except (IOError, OSError), err:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': str(type(err)),
                                'detail': str(err)}),
                    content_type='application/json', status=403)
        else:
            response = MunkiFile.list(kind)
            return HttpResponse(json.dumps(response) + '\n',
                                content_type='application/json')

    if request.META.has_key('HTTP_X_METHODOVERRIDE'):
        # support browsers/libs that don't directly support the other verbs
        http_method = request.META['HTTP_X_METHODOVERRIDE']
        if http_method.lower() == 'put':
            request.method = 'PUT'
            request.META['REQUEST_METHOD'] = 'PUT'
            request.PUT = QueryDict(request.body)
        if http_method.lower() == 'delete':
            request.method = 'DELETE'
            request.META['REQUEST_METHOD'] = 'DELETE'
            request.DELETE = QueryDict(request.body)
        if http_method.lower() == 'patch':
            request.method = 'PATCH'
            request.META['REQUEST_METHOD'] = 'PATCH'
            request.PATCH = QueryDict(request.body)

    if request.method == 'POST':
        LOGGER.debug("Got API POST request for %s", kind)
        if not request.user.has_perm('pkgsinfo.create_pkginfofile'):
            raise PermissionDenied
        filename = request.POST.get('filename') or filepath
        filedata = request.FILES.get('filedata')
        if not (filename and filedata):
            # malformed request
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'BadRequest',
                            'detail': 'Missing filename or filedata'}),
                content_type='application/json', status=400)
        try:
            MunkiFile.new(kind, filedata, filename, request.user)
        except FileError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        else:
            return HttpResponse(
                json.dumps({'filename': filename}),
                content_type='application/json', status=200)

    if request.method in ('PUT', 'PATCH'):
        LOGGER.debug("Got API %s request for %s", request.method, kind)
        response = HttpResponse(
            json.dumps({'result': 'failed',
                        'exception_type': 'NotAllowed',
                        'detail': 'This method is not supported'}),
            content_type='application/json', status=405)
        response['Allow'] = 'GET, POST, DELETE'
        return response

    if request.method == 'DELETE':
        LOGGER.debug("Got API DELETE request for %s", kind)
        if not request.user.has_perm('pkgsinfo.delete_pkginfofile'):
            raise PermissionDenied
        if not filepath:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'MassDeleteNotSupported',
                            'detail': 'Deleting all items is not supported'}
                          ),
                content_type='application/json', status=403)
        try:
            MunkiFile.delete(kind, filepath, request.user)
        except FileDoesNotExistError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=404)
        except FileDeleteError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        except FileError, err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        else:
            # success
            return HttpResponse(status=204)

@csrf_exempt
@logged_in_or_basicauth()
def db_api(request, kind, serial_number=None):
    if kind not in ['report', 'inventory', 'imagr']:
        return HttpResponse(status=404)

    response_type = 'json'
    if request.META.get('HTTP_ACCEPT') == 'application/xml':
        response_type = 'xml'
    
    if request.method == 'GET':
        LOGGER.debug("Got API GET request for %s", kind)

        filter_terms = request.GET.copy()
        if '_' in filter_terms.keys():
            del filter_terms['_']
        if 'api_fields' in filter_terms.keys():
            api_fields = filter_terms['api_fields'].split(',')
            del filter_terms['api_fields']
        else:
            api_fields = None

        response = list()
        if serial_number:
            try:
                if kind == "report":
                    item_list = serializers.serialize('python', Machine.objects.filter(serial_number=serial_number), fields=(api_fields))
                elif kind == "imagr":
                    item_list = serializers.serialize('python', ImagrReport.objects.filter(machine=Machine.objects.get(serial_number=serial_number)), fields=(api_fields))
            except Machine.DoesNotExist:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': 'MachineDoesNotExist',
                                'detail': '%s does not exist' % serial_number}),
                    content_type='application/json', status=404)
        else:
            if kind == "report":
                item_list = serializers.serialize('python', Machine.objects.all(), fields=(api_fields))
            elif kind == "imagr":
                item_list = serializers.serialize('python', ImagrReport.objects.all(), fields=(api_fields))

        for item in item_list:
            if serial_number == item["pk"]:
                response = item['fields']
            else:
                if api_fields and 'serial' in api_fields:
                    item['fields']['serial'] = item['pk']
                response.append(item['fields'])

        if response_type == 'json':
            response = convert_dates_to_strings(response)
            return HttpResponse(
                json.dumps(response) + '\n',
                content_type='application/json', status=201)
        else:
            return HttpResponse(
                response,
                content_type='application/xml', status=201)
    
    if request.META.has_key('HTTP_X_METHODOVERRIDE'):
        # support browsers/libs that don't directly support the other verbs
        http_method = request.META['HTTP_X_METHODOVERRIDE']
        if http_method.lower() == 'delete':
            request.method = 'DELETE'
            request.META['REQUEST_METHOD'] = 'DELETE'
            request.DELETE = QueryDict(request.body)

    if request.method == 'POST':
        try:
            submit = json.loads(request.body)
        except:
            submit = request.POST
        
        submission_type = submit.get('submission_type')

        if not serial_number:
            serial_number = submit.get('serial')

        if serial_number:
            try:
                machine = Machine.objects.get(serial_number=serial_number)
            except Machine.DoesNotExist:
                machine = Machine(serial_number=serial_number)
            try:
                report = MunkiReport.objects.get(machine=machine)
            except MunkiReport.DoesNotExist:
                report = MunkiReport(machine=machine)

            if machine and report:
                machine.remote_ip = request.META['REMOTE_ADDR']
                report.activity = ""

                if 'name' in submit:
                    machine.hostname = submit.get('name')
                if 'username' in submit:
                    machine.username = submit.get('username')
                if 'unit' in submit:
                    unit = BusinessUnit.objects.get(hash=submit.get('unit'))
                    machine.businessunit = unit

                if 'base64bz2report' in submit:
                    #print submit.get('base64bz2report')
                    report.update_report(submit.get('base64bz2report'))

                # extract machine data from the report
                report_data = report.get_report()
                if 'MachineInfo' in report_data:
                    machine.os_version = report_data['MachineInfo'].get('os_vers', machine.os_version)
                    machine.cpu_arch = report_data['MachineInfo'].get('arch', machine.cpu_arch)

                hwinfo = {}
                if 'SystemProfile' in report_data.get('MachineInfo', []):
                    if 'SPHardwareDataType' in report_data['MachineInfo']['SystemProfile'][0].keys():
                        hwinfo = report_data['MachineInfo']['SystemProfile'][0]['SPHardwareDataType'][0]

                if hwinfo:
                    machine.machine_model = hwinfo.get('machine_model') and hwinfo.get('machine_model') or machine.machine_model
                    machine.cpu_type = hwinfo.get('cpu_type') and hwinfo.get('cpu_type') or machine.cpu_type
                    machine.cpu_speed = hwinfo.get('current_processor_speed') and hwinfo.get('current_processor_speed') or machine.cpu_speed
                    machine.ram = hwinfo.get('physical_memory') and hwinfo.get('physical_memory') or machine.ram

                report.runtype = submit.get('runtype', 'UNKNOWN')
                
                imagrReport = None
                if submit.get('imagr_workflow'):
                    machine.imagr_workflow = submit.get('imagr_workflow')
                if submit.get('status') and submit.get('message'):
                    machine.current_status = submit.get('status')
                    imagrReport = ImagrReport(machine=machine, message=submit.get('message'), status=submit.get('status'))
                    report.runstate = u"imagr"
                # delete pending workflow if successful ended
                if submit.get('status') == 'success' or submit.get('status') == 'error':
                    machine.imagr_workflow = ""

                if submission_type == 'postflight':
                    report.runstate = u"done"

                if submission_type == 'preflight':
                    report.runstate = u"in progress"
                    report.activity = report.encode({"Updating": "preflight"})

                if submission_type == 'report_broken_client':
                    report.runstate = u"broken client"
                    report.errors = 1
                    report.warnings = 0
                
                # setting hostname if there isn't set one / prevent save issues
                if machine.hostname == "unknown":
                    machine.hostname = serial_number

                report.timestamp = timezone.now()
                machine.save()
                report.save()

                # save imagr report
                if imagrReport:
                    imagrReport.save()
                
                return HttpResponse(status=204)
        return HttpResponse(status=404)

    if request.method == 'DELETE':
        LOGGER.debug("Got API DELETE request for %s", kind)
        if not request.user.has_perm('reports.delete_machine'):
            raise PermissionDenied
        if not serial_number:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'MassDeleteNotSupported',
                            'detail': 'Deleting all items is not supported'}
                        ),
                content_type='application/json', status=403)
        try:
            Machine.objects.filter(serial_number=serial_number).delete()
        except Machine.DoesNotExist:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': 'MachineDoesNotExist',
                                'detail': '%s does not exist' % serial_number}),
                    content_type='application/json', status=404)
        else:
            # success
            return HttpResponse(status=204)