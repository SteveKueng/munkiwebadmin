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
from django.conf import settings
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

from api.models import Plist, MunkiFile
from api.models import FileError, FileWriteError, FileReadError, \
                       FileAlreadyExistsError, \
                       FileDoesNotExistError, FileDeleteError

from reports.models import Machine, MunkiReport, Spectre
from inventory.models import Inventory, InventoryItem
from vault.models import localAdmin, passwordAccess
from munkiwebadmin.django_basic_auth import logged_in_or_basicauth

import datetime
import json
import logging
import os
import mimetypes
import plistlib
import re
import base64
import bz2
import hashlib
import zlib
import requests
import simpleMDMpy
from multiprocessing.pool import ThreadPool

LOGGER = logging.getLogger('munkiwebadmin')

try:
    simpleMDMKey = settings.SIMPLEMDMKEY
except AttributeError:
    simpleMDMKey = ""

try:
    PROXY_ADDRESS = settings.PROXY_ADDRESS
except AttributeError:
    PROXY_ADDRESS = ""

try:
    SPECTRE_URLS = settings.SPECTRE_URLS
except AttributeError:
    SPECTRE_URLS = ""

try:
    CONVERT_TO_QWERTZ = settings.CONVERT_TO_QWERTZ
except AttributeError:
    CONVERT_TO_QWERTZ = False

proxies = {}
if PROXY_ADDRESS != "":
    proxies = {
        "http": 'http://'+PROXY_ADDRESS,
        "https": 'https://'+PROXY_ADDRESS
    }

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


def convert_to_qwertz(string):
    newString = ""
    for c in string:
        if c == "z":
            c = "y"
        elif c == "Z":
            c = "Y"
        elif c == "y":
            c = "z"
        elif c == "Y":
            c = "Z"
        newString = newString + c
    return newString


def convert_html_to_json(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    try:
        data = json.loads(cleantext.strip())
    except (ValueError, KeyError, TypeError):
        data = ""
    return data


def decode_to_string(data):
    '''Decodes an inventory submission, which is a plist-encoded
    list, compressed via bz2 and base64 encoded.'''
    try:
        bz2data = base64.b64decode(data)
        return bz2.decompress(bz2data)
    except Exception:
        return None


def getDataFromAPI(URL):
    try:
        response = requests.get(URL, timeout=10)
    except requests.exceptions.Timeout:
        pass
    else:
        if response.status_code in [200, 201, 202, 203, 204]:
            response.encoding = "utf-8-sig"
            return convert_html_to_json(response.text)
    return None


def postDataAPI(URL, postData):
    try:
        response = requests.post(URL, timeout=10, data=json.dumps(postData))
    except requests.exceptions.Timeout:
        pass
    else:
        if response.status_code in [200, 201, 202, 203, 204]:
            response.encoding = "utf-8-sig"
            return convert_html_to_json(response.text)
    return None


def getSimpleMDMID(apiKey, serial_number):
    """ returns device ID for your device """
    devices = simpleMDMpy.devices(apiKey)
    devices.proxyDict = proxies
    response = devices.getDevice(search=serial_number)
    if response.status_code in range(200,207):
        for data in response.json()['data']:
            return data.get('id')
    return None


def getSimpleMDMDevice(apiKey, ID):
    """ returns device info for your device """
    devices = simpleMDMpy.devices(apiKey)
    devices.proxyDict = proxies
    response = devices.getDevice(deviceID=ID)
    if response.status_code in range(200,207):
        return response.json()
    return None


def getSimpleMDMDeviceGroups(apiKey):
    """ returns device info for your device """
    deviceGroups = simpleMDMpy.deviceGroups(apiKey)
    deviceGroups.proxyDict = proxies
    response = deviceGroups.getDeviceGroup()
    if response.status_code in range(200,207):
        return response.json()
    return None

def getSimpleMDMAppGroups(apiKey):
    """ returns device info for your device """
    appGroups = simpleMDMpy.appGroups(apiKey)
    appGroups.proxyDict = proxies
    response = appGroups.getAppGroup()
    if response.status_code in range(200,207):
        return response.json()
    return None


def setSimpleMDMName(apiKey, deviceID, deviceName):
    """ sets device name in simpleMDM """
    devices = simpleMDMpy.devices(apiKey)
    devices.proxyDict = proxies
    if devices.updateDevice(deviceName, str(deviceID)).status_code == 200:
        return True
    return False


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
        if kind == 'manifests':
            if not request.user.has_perm('manifests.view_manifestfile'):
                raise PermissionDenied
        if kind in ('catalogs', 'pkgsinfo', 'icons'):
            if not request.user.has_perm('pkgsinfo.view_pkginfofile'):
                raise PermissionDenied
        if filepath:
            try:
                response = Plist.read(kind, filepath)
            except FileDoesNotExistError, err:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': str(type(err)),
                                'detail': str(err)}),
                    content_type='application/json', status=404)
            except FileReadError, err:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': str(type(err)),
                                'detail': str(err)}),
                    content_type='application/json', status=403)
            if response_type == 'json':
                response = [convert_dates_to_strings(response)]
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
                    if response_type == 'json':
                        plist = convert_dates_to_strings(plist)
                    if kind == 'catalogs':
                        # catalogs are list objects, not dicts
                        plist = {'contents': plist}
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
        if kind in ('catalogs', 'pkgsinfo'):
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
        if kind in ('catalogs', 'pkgsinfo'):
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
            LOGGER.debug("plist data %s", request_data)
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
        if kind in ('catalogs', 'pkgsinfo'):
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
        if kind == 'catalogs':
            if not request.user.has_perm('pkgsinfo.change_pkginfofile'):
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

    return HttpResponse(status=404)

@csrf_exempt
@logged_in_or_basicauth()
def file_api(request, kind, filepath=None):
    '''Basic API calls for working with non-plist Munki files'''
    if kind not in ['icons', 'pkgs']:
        return HttpResponse(status=404)

    response_type = 'json'
    if request.META.get('HTTP_ACCEPT') == 'application/xml':
        response_type = 'xml_plist'

    if request.method == 'GET':
        LOGGER.debug("Got API GET request for %s", kind)
        if not request.user.has_perm('pkgsinfo.view_pkginfofile'):
            raise PermissionDenied
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

    if request.method in ('POST', 'PUT'):
        LOGGER.debug("Got API %s request for %s", request.method, kind)
        if not request.user.has_perm('pkgsinfo.change_pkginfofile'):
            LOGGER.error("permission denied")
            raise PermissionDenied
        if request.method == 'POST':
            filename = request.POST.get('filename') or filepath
            filedata = request.FILES.get('filedata')
        else:
            filename = filepath
            filedata = request.body
            if "data:image/png;base64" in filedata:
                img = filedata.split(',')[1]
                filedata = img.decode('base64')
        if not (filename and filedata):
            # malformed request
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'BadRequest',
                            'detail': 'Missing filename or filedata'}),
                content_type='application/json', status=400)
        try:
            if request.method == 'POST':
                MunkiFile.new(kind, filedata, filename, request.user)
            else:
                MunkiFile.writedata(kind, filedata, filename, request.user)
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

    if request.method == 'PATCH':
        LOGGER.debug("Got API PATCH request for %s", kind)
        response = HttpResponse(
            json.dumps({'result': 'failed',
                        'exception_type': 'NotAllowed',
                        'detail': 'This method is not supported'}),
            content_type='application/json', status=405)
        response['Allow'] = 'GET, POST, PUT, DELETE'
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
def db_api(request, kind, subclass=None, serial_number=None):
    if kind not in ['report', 'vault', 'inventory']:
        return HttpResponse(status=404)

    # ------- get submit -------
    try:
        submit = json.loads(request.body)
    except:
        submit = request.POST
    
    submission_type = submit.get('submission_type', None)

    # ----------- RESPONSE TYPE -----------------
    response_type = 'json'
    if request.META.get('HTTP_ACCEPT') == 'application/xml':
        response_type = 'xml'

    # ----------- GET -----------------
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
        if kind in ['report']:
            if not request.user.has_perm('reports.can_view_reports'):
                raise PermissionDenied
            if serial_number:
                try:
                    item_list = serializers.serialize(response_type, Machine.objects.filter(serial_number=serial_number), fields=(api_fields))
                except Machine.DoesNotExist:
                    return HttpResponse(
                        json.dumps({'result': 'failed',
                                    'exception_type': 'MachineDoesNotExist',
                                    'detail': '%s does not exist' % serial_number}),
                        content_type='application/json', status=404)
            else:
                item_list = serializers.serialize(response_type, Machine.objects.all(), fields=(api_fields))

            return HttpResponse(
                item_list,
                content_type='application/'+response_type, status=201)
        
        if kind in ['vault'] and subclass == "reasons" and serial_number:
            if not request.user.has_perm('vault.view_passwordAccess'):
                raise PermissionDenied
            try:
                access = passwordAccess.objects.filter(machine=Machine.objects.get(serial_number=serial_number))
            except Machine.DoesNotExist:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': 'MachineDoesNotExist',
                                'detail': '%s does not exist' % serial_number}),
                    content_type='application/json', status=404)
            

            if response_type == 'json':
                response = serializers.serialize('json', access, fields=(api_fields), indent=2, use_natural_foreign_keys=True,  use_natural_primary_keys=True)
            else:
                response = serializers.serialize('xml', access, fields=(api_fields), indent=2, use_natural_foreign_keys=True,  use_natural_primary_keys=True)
            return HttpResponse(
                response,
                content_type='application/'+response_type, status=201)

        if kind in ['vault'] and subclass == "expire" and serial_number:
            if not request.user.has_perm('vault.view_expireDate'):
                raise PermissionDenied
            try:
                localadmin = localAdmin.objects.filter(machine=Machine.objects.get(serial_number=serial_number))
            except Machine.DoesNotExist:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': 'MachineDoesNotExist',
                                'detail': '%s does not exist' % serial_number}),
                    content_type='application/json', status=404)
            
            if response_type == 'json':
                response = serializers.serialize('json', localadmin, fields=(['expireDate']))
            else:
                response = serializers.serialize('xml', localadmin, fields=(['expireDate']))
            return HttpResponse(
                response[1:-1],
                content_type='application/'+response_type, status=200)
    
    # ----------- HTTP_X_METHODOVERRIDE -----------------
    if request.META.has_key('HTTP_X_METHODOVERRIDE'):
        # support browsers/libs that don't directly support the other verbs
        http_method = request.META['HTTP_X_METHODOVERRIDE']
        if http_method.lower() == 'delete':
            request.method = 'DELETE'
            request.META['REQUEST_METHOD'] = 'DELETE'
            request.DELETE = QueryDict(request.body)

    # ----------- POST -----------------
    if request.method == 'POST':
        LOGGER.debug("Got API POST request for %s", kind)
        if serial_number:
            try:
                machine = Machine.objects.get(serial_number=serial_number)
            except Machine.DoesNotExist:
                machine = Machine(serial_number=serial_number)
            if kind in ['report']:
                if not request.user.has_perm('reports.change_machine'):
                    raise PermissionDenied
                try:
                    report = MunkiReport.objects.get(machine=machine)
                except MunkiReport.DoesNotExist:
                    report = MunkiReport(machine=machine)

                if machine and report:
                    machine.remote_ip = request.META['REMOTE_ADDR']
                    report.activity = ""

                    if not machine.hostname and 'name' in submit:
                        machine.hostname = submit.get('name')
                    if 'username' in submit:
                        machine.username = submit.get('username')
                    if 'unit' in submit:
                        unit = BusinessUnit.objects.get(hash=submit.get('unit'))
                        machine.businessunit = unit

                    if 'base64bz2report' in submit:
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
                        machine.machine_model = hwinfo.get('machine_model', machine.machine_model)
                        machine.cpu_type = hwinfo.get('cpu_type', machine.cpu_type)
                        machine.cpu_speed = hwinfo.get('current_processor_speed', machine.cpu_speed)
                        machine.ram = hwinfo.get('physical_memory', machine.ram)
                    
                    # 
                    if not machine.os_version:
                        machine.os_version = "unknown"
                    if not machine.machine_model:
                        machine.machine_model = "unknown"

                    report.runtype = submit.get('runtype', 'UNKNOWN')

                    if submission_type == 'postflight':
                        report.runstate = u"done"

                    if submission_type == 'preflight':
                        report.runstate = u"in progress"
                        report.activity = report.encode({"Updating": "preflight"})

                    if submission_type == 'report_broken_client':
                        report.runstate = u"broken client"
                        report.errors = 1
                        report.warnings = 0

                    # simpleMDM
                    if simpleMDMKey:
                        LOGGER.debug("simpleMDM connnect")
                        try:
                            simpleMDMID = getSimpleMDMID(simpleMDMKey, serial_number)
                        except Exception as e:
                            LOGGER.error(e)
                        else:
                            machine.simpleMDMID = simpleMDMID
                            LOGGER.debug("simpleMDM device id %s", machine.simpleMDMID)
                            setSimpleMDMName(simpleMDMKey, machine.simpleMDMID, machine.hostname)

                    report.timestamp = timezone.now()
                    try:
                        machine.save()
                    except Exception as e:
                        LOGGER.error("machine save error: %s", e)
                    try:
                        report.save()
                    except Exception as e:
                        LOGGER.error("report save error: %s", e)

            elif kind in ['inventory']:
                # list of bundleids to ignore
                bundleid_ignorelist = [
                    'com.apple.print.PrinterProxy'
                ]
                if machine:
                    compressed_inventory = submit.get('base64bz2inventory')
                    if compressed_inventory:
                        compressed_inventory = compressed_inventory.replace(" ", "+")
                        inventory_str = decode_to_string(compressed_inventory)
                        try:
                            inventory_list = plistlib.readPlistFromString(inventory_str)
                        except Exception:
                            inventory_list = None
                        if inventory_list:
                            LOGGER.debug(inventory_list)
                            try:
                                inventory_meta = Inventory.objects.get(machine=machine)
                            except Inventory.DoesNotExist:
                                inventory_meta = Inventory(machine=machine)
                            inventory_meta.sha256hash = \
                                hashlib.sha256(inventory_str).hexdigest()
                            # clear existing inventoryitems
                            machine.inventoryitem_set.all().delete()
                            # insert current inventory items
                            for item in inventory_list:
                                # skip items in bundleid_ignorelist.
                                if not item.get('bundleid') in bundleid_ignorelist:
                                    i_item = machine.inventoryitem_set.create(
                                        name=item.get('name', ''),
                                        version=item.get('version', ''),
                                        bundleid=item.get('bundleid', ''),
                                        bundlename=item.get('CFBundleName', ''),
                                        path=item.get('path', '')
                                        )
                            inventory_meta.save()
                        return HttpResponse(status=200)
                return HttpResponse(status=404)

            elif kind in ['vault'] and subclass == "set":
                if not request.user.has_perm('vault.change_localadmin'):
                    raise PermissionDenied
                # set password
                value = submit.get('value', None)
                value = base64.b64decode(value)
                if value:
                    try:
                        localadmin = localAdmin.objects.get(machine=machine)
                    except localAdmin.DoesNotExist:
                        localadmin = localAdmin(machine=machine)
                    localadmin.setPassword(value)
                    localadmin.save()
                else:
                    return HttpResponse(
                        json.dumps({'result': 'failed',
                                    'exception_type': 'BadRequest',
                                    'detail': 'Missing value'}),
                        content_type='application/json', status=400)

            elif kind in ['vault'] and subclass == "show":
                if not request.user.has_perm('vault.show_password'):
                    raise PermissionDenied
                reason = submit.get('reason', None)
                if reason:
                    try:
                        localadmin = localAdmin.objects.get(machine=Machine.objects.get(serial_number=serial_number))
                        password = localadmin.getPassword(request.user, reason)
                    except Machine.DoesNotExist:
                        return HttpResponse(
                            json.dumps({'result': 'failed',
                                        'exception_type': 'MachineDoesNotExist',
                                        'detail': '%s does not exist' % serial_number}),
                            content_type='application/json', status=404)
                    
                    if response_type == 'json':
                        return HttpResponse(
                            json.dumps(password) + '\n',
                            content_type='application/json', status=201)
                    else:
                        return HttpResponse(
                            password,
                            content_type='application/xml', status=201)
                else:
                    return HttpResponse(
                        json.dumps({'result': 'failed',
                                    'exception_type': 'BadRequest',
                                    'detail': 'Missing reason'}),
                        content_type='application/json', status=400)
            else:
                return HttpResponse(status=404)
            return HttpResponse(status=204)

        return HttpResponse(status=404)
    # ----------- PUT -----------------
    if request.method == 'PUT':
        LOGGER.debug("Got API PUT request for %s", kind)
        if not request.user.has_perm('reports.change_machine'):
            raise PermissionDenied
        if serial_number:
            try:
                machine = Machine.objects.get(serial_number=serial_number)
            except Machine.DoesNotExist:
                machine = Machine(serial_number=serial_number)

            if 'name' in submit:
                machine.hostname = submit.get('name')
                machine.save()
                return HttpResponse(status=201)

    # ----------- DELETE -----------------
    elif request.method == 'DELETE':
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
    
    # ----------- error 404 -----------------
    return HttpResponse(status=404)

@csrf_exempt
@logged_in_or_basicauth()
def mdm_api(request, kind, submission_type, primary_id=None, action=None, secondary_id=None):
    LOGGER.debug("Got API request for %s, %s, %s, %s" % (kind, submission_type, primary_id, secondary_id))
    if kind not in ['mdm']:
        return HttpResponse(status=404)
    
    # ----------- RESPONSE TYPE -----------------
    response_type = 'json'
    if request.META.get('HTTP_ACCEPT') == 'application/xml':
        response_type = 'xml'
    
    if request.method == 'GET':
        LOGGER.debug("Got API GET request for %s", kind)

        if not request.user.has_perm('reports.can_view_reports'):
            raise PermissionDenied

        data = None        
        if submission_type == "device_groups":
            data = getSimpleMDMDeviceGroups(simpleMDMKey)
        
        if submission_type == "app_groups":
            data = getSimpleMDMAppGroups(simpleMDMKey)
        
        if submission_type == "devices" and primary_id:
            try:
                machine = Machine.objects.get(serial_number=primary_id)
            except Machine.DoesNotExist:
                return HttpResponse(status=204)
            
            if not machine.simpleMDMID:
                return HttpResponse(status=204)
            
            data = getSimpleMDMDevice(simpleMDMKey, machine.simpleMDMID)
            
            if CONVERT_TO_QWERTZ:
                # layout fix
                firmware_password = data['data']['attributes'].get('firmware_password')
                if firmware_password:
                    data['data']['attributes']['firmware_password'] = convert_to_qwertz(firmware_password)
        
        if data:
            if response_type == 'json':
                return HttpResponse(
                    json.dumps(data) + '\n',
                    content_type='application/json')
            else:
                return HttpResponse(
                    plistlib.writePlistToString(data),
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
        if not request.user.has_perm('reports.change_machine'):
            raise PermissionDenied
        
        # ------- get submit -------
        if submission_type == "devices" and primary_id:
            try:
                machine = Machine.objects.get(serial_number=primary_id)
            except Machine.DoesNotExist:
                return HttpResponse(
                        json.dumps({'result': 'failed',
                                    'exception_type': 'MachineDoesNotExist',
                                    'detail': '%s does not exist' % serial_number}),
                        content_type='application/json', status=404)
            
            if not machine.simpleMDMID:
                return HttpResponse(
                        json.dumps({'result': 'failed',
                                    'exception_type': 'MachineDoesNotExist',
                                    'detail': '%s has no simplMDM ID' % serial_number}),
                        content_type='application/json', status=404)

            devices = simpleMDMpy.devices(simpleMDMKey)
            devices.proxyDict = proxies
            response = None

            if action == "restart":
                response = devices.restcartDevice(deviceID=machine.simpleMDMID)
            
            if action == "shutdown":
                response = devices.shutdownDevice(deviceID=machine.simpleMDMID)
                
            if action == "lock":
                try:
                    LOCK_MESSAGE = settings.LOCK_MESSAGE
                except AttributeError:
                    LOCK_MESSAGE = ""
                try:
                    IT_NUMBER = settings.IT_NUMBER
                except AttributeError:
                    IT_NUMBER = ""
                try:
                    PIN = settings.PIN
                except AttributeError:
                    PIN = ""
                response = devices.lockDevice(deviceID=machine.simpleMDMID, message=LOCK_MESSAGE, phone_number=IT_NUMBER, pin=PIN)

            if action == "refresh":
                response = devices.refreshDevice(deviceID=machine.simpleMDMID)

        if submission_type == "device_groups" and action == "devices":
            if primary_id and secondary_id:
                deviceGroups = simpleMDMpy.deviceGroups(simpleMDMKey)
                deviceGroups.proxyDict = proxies
                response = deviceGroups.assignDevice(deviceID=secondary_id, deviceGoupID=primary_id)
            else:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': 'BadRequest',
                                'detail': 'Missing group'}),
                    content_type='application/json', status=400)

        if submission_type == "app_groups": 
            if action == "push_apps":
                if primary_id:
                    appGroups = simpleMDMpy.appGroups(simpleMDMKey)
                    appGroups.proxyDict = proxies
                    response = appGroups.pushApps(appGroupID=primary_id)
                else:
                    return HttpResponse(
                        json.dumps({'result': 'failed',
                                    'exception_type': 'BadRequest',
                                    'detail': 'Missing group'}),
                        content_type='application/json', status=400)
            if action == "devices":
                if primary_id and secondary_id:
                    appGroups = simpleMDMpy.appGroups(simpleMDMKey)
                    appGroups.proxyDict = proxies
                    response = appGroups.assignDevice(appGroupID=primary_id, deviceID=secondary_id)
                else:
                    return HttpResponse(
                        json.dumps({'result': 'failed',
                                    'exception_type': 'BadRequest',
                                    'detail': 'Missing group'}),
                        content_type='application/json', status=400)

    if request.method == 'DELETE':
        LOGGER.debug("Got API DELETE request for %s", kind)
        if not request.user.has_perm('reports.change_machine'):
            raise PermissionDenied
        if submission_type == "app_groups" and action == "devices":
            if primary_id and secondary_id:
                appGroups = simpleMDMpy.appGroups(simpleMDMKey)
                appGroups.proxyDict = proxies
                response = appGroups.unAssignDevice(appGroupID=primary_id, deviceID=secondary_id)
                LOGGER.debug(response)
            else:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': 'BadRequest',
                                'detail': 'Missing group'}),
                    content_type='application/json', status=400)
    
    if response:
        try:
            content_type = response.headers['Content-Type']
        except:
            content_type = None
            
        return HttpResponse(
                    content=response.content,
                    status=response.status_code,
                    content_type=content_type
                )

    # ----------- error 404 -----------------
    return HttpResponse(status=404)

@csrf_exempt
@logged_in_or_basicauth()
def spectre_api(request, kind, submission_type, id=None):
    LOGGER.debug("Got API request for %s, %s:%s" % (kind, submission_type, id))
    if kind not in ['spectre']:
        return HttpResponse(status=404)
    
    # ------- get submit -------
    try:
        submit = json.loads(request.body)
    except:
        submit = request.POST

    if request.method == 'GET':
        LOGGER.debug("Got API GET request for %s", kind)

        if not request.user.has_perm('reports.can_view_spectre'):
            raise PermissionDenied

        if SPECTRE_URLS != "":
            if submission_type == "user" and id:
                spectreData = {}
                pool = ThreadPool(processes=2)

                if SPECTRE_URLS.get('AD'):
                    URL = SPECTRE_URLS['AD'] + "?username=" + id
                    AD = pool.apply_async(getDataFromAPI, (URL, ))

                if SPECTRE_URLS.get('SCSM'):
                    URL = SPECTRE_URLS['SCSM'] + "?username=" + id
                    SCSM = pool.apply_async(getDataFromAPI, (URL, ))

                # wait for answer
                if SPECTRE_URLS.get('AD'):
                    spectreData["AD"] = AD.get()
                if SPECTRE_URLS.get('SCSM'):
                    spectreData["SCSM"] = SCSM.get()

                if spectreData:
                    return HttpResponse(
                            content=json.dumps(spectreData, ensure_ascii=False, sort_keys=True, cls=DjangoJSONEncoder, default=str),
                            status=200,
                            content_type='application/json'
                        )
            
            if submission_type == "users":
                spectreData = {}
                pool = ThreadPool(processes=2)

                if SPECTRE_URLS.get('SCSM'):
                    URL = SPECTRE_URLS['SCSM'] + "?username=all"
                    SCSM = pool.apply_async(getDataFromAPI, (URL, ))

                if SPECTRE_URLS.get('SCSM'):
                    spectreData = SCSM.get()

                if spectreData:
                    return HttpResponse(
                            content=json.dumps(spectreData, ensure_ascii=False, sort_keys=True, cls=DjangoJSONEncoder, default=str),
                            status=200,
                            content_type='application/json'
                        )

            if submission_type == "computer" and id:
                spectreData = {}
                pool = ThreadPool(processes=3)

                if SPECTRE_URLS.get('SCSM'):
                    URL = SPECTRE_URLS['SCSM'] + "?computername=" + id
                    SCSM = pool.apply_async(getDataFromAPI, (URL, ))
                
                try:
                    spectreData['os'] =  "macOS"
                    machine = Machine.objects.get(hostname=id)
                    spectreData['Munki'] = model_to_dict(machine)
                except Machine.DoesNotExist:
                    machine = {}
                    spectreData['os'] =  "Windows"

                if spectreData['os'] == "macOS":
                    try:
                        report = MunkiReport.objects.get(machine=machine)
                        spectreData['Munki']['report'] = report.get_report()
                    except MunkiReport.DoesNotExist:
                        spectreData['Munki']['report'] = ""
                
                    if machine.simpleMDMID:
                        spectreData['MDM'] = getSimpleMDMDevice(simpleMDMKey, machine.simpleMDMID)['data']
                
                if spectreData['os'] == "Windows":
                    if SPECTRE_URLS.get('AD'):
                        URL = SPECTRE_URLS['AD'] + "?computername=" + id
                        AD = pool.apply_async(getDataFromAPI, (URL, ))

                    if SPECTRE_URLS.get('SCCM'):
                        URL = SPECTRE_URLS['SCCM'] + "?computername=" + id
                        SCCM = pool.apply_async(getDataFromAPI, (URL, ))

                    if SPECTRE_URLS.get('AD'):
                        spectreData["AD"] = AD.get()
                    if SPECTRE_URLS.get('SCCM'):
                        spectreData["SCCM"] = SCCM.get()

                if SPECTRE_URLS.get('SCSM'):
                    spectreData["SCSM"] = SCSM.get()

                if spectreData:
                    return HttpResponse(
                            content=json.dumps(spectreData, ensure_ascii=False, sort_keys=True, cls=DjangoJSONEncoder, default=str),
                            status=200,
                            content_type='application/json'
                        )

            if submission_type == "computers":
                spectreData = {}
                pool = ThreadPool(processes=2)

                if SPECTRE_URLS.get('SCSM'):
                    URL = SPECTRE_URLS['SCSM'] + "?computername=all"
                    SCSM = pool.apply_async(getDataFromAPI, (URL, ))

                if SPECTRE_URLS.get('SCSM'):
                    spectreData = SCSM.get()

                if spectreData:
                    return HttpResponse(
                            content=json.dumps(spectreData, ensure_ascii=False, sort_keys=True, cls=DjangoJSONEncoder, default=str),
                            status=200,
                            content_type='application/json'
                        )
                        
    
    if request.method == 'POST':
        LOGGER.debug("Got API POST request for %s", kind)

        if not request.user.has_perm('reports.change_spectre'):
            raise PermissionDenied
        
        if submission_type == "user" and id:
            backendTarget = submit.get("backendTarget")
            LOGGER.debug("backendTarget: %s", backendTarget)

            SPECTRE_URL = SPECTRE_URLS.get(backendTarget, None)
            LOGGER.debug("SPECTRE_URL: %s", SPECTRE_URL)
            if SPECTRE_URL:
                URL = SPECTRE_URL + "?username=" + id
                USERDATA = pool.apply_async(postDataAPI, (URL, submit))

                # wait for answer
                spectreData = USERDATA.get()

                LOGGER.debug("spectreData: %s", spectreData)
                if spectreData:
                    return HttpResponse(
                            content=json.dumps(spectreData, ensure_ascii=False, sort_keys=True, cls=DjangoJSONEncoder, default=str),
                            status=200,
                            content_type='application/json')

        if submission_type == "computer" and id:
            backendTarget = submit.get("backendTarget")

            SPECTRE_URL = SPECTRE_URLS.get(backendTarget, None)
            if backendTarget:
                URL = SPECTRE_URL + "?computer=" + id
                COMPUTERDATA = pool.apply_async(postDataAPI, (URL, submit))

                # wait for answer
                spectreData = COMPUTERDATA.get()

                if spectreData:
                    return HttpResponse(
                            content=json.dumps(spectreData, ensure_ascii=False, sort_keys=True, cls=DjangoJSONEncoder, default=str),
                            status=200,
                            content_type='application/json')


    # ----------- error 404 -----------------
    return HttpResponse(status=404)


@csrf_exempt
@logged_in_or_basicauth()
def santa_api(request, kind, submission_type, machine_id):
    LOGGER.debug("Got API request for %s, %s:%s" % (kind, submission_type, machine_id))


    payload = request.body
    content_encoding = request.META.get('HTTP_CONTENT_ENCODING', None)
    if content_encoding:
        payload = json.loads(zlib.decompress(payload))

    LOGGER.debug(payload)

    if submission_type == "preflight":
        contend = { 'machine_id': machine_id,
                'batch_size': 20,
                #'upload_logs_url': 'http://localhost:8000/api/santa/log/' + payload["serial_num"]
                }
        return HttpResponse(
                            json.dumps(contend) + '\n',
                            content_type='application/json', status=200)

    if submission_type == "log":
        contend = {'machine_id': machine_id }
        return HttpResponse(
                            json.dumps(contend),
                            content_type='application/json', status=200)

    if submission_type == "ruledownload":
        contend = { "client_mode": "MONITOR", "rules": { "rule_type": "BINARY", "policy": "BLACKLIST", "sha256": "0494fb788198359df09179bc4ce32b8e93b59e64f518c001cd64a7f2ff1e5c38", "custom_msg": "blacklist SourceTree" } }
        return HttpResponse(
                            json.dumps(contend),
                            content_type='application/json', status=200)

    if submission_type == "eventupload":
        return HttpResponse(status=200)

    if submission_type == "postflight":
        return HttpResponse(status=200)
