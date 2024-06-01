"""
api/views.py
"""
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from rest_framework.mixins import (
    CreateModelMixin, 
    DestroyModelMixin,
    UpdateModelMixin,
    ListModelMixin
)
from rest_framework.permissions import DjangoModelPermissions

from django.http import HttpResponse, QueryDict, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.conf import settings

from api.models import Plist, MunkiFile
from api.models import FileError, FileWriteError, FileReadError, \
                       FileAlreadyExistsError, \
                       FileDoesNotExistError, FileDeleteError

from reports.models import Machine
from manifests.models import ManifestFile
from pkgsinfo.models import PkginfoFile
from catalogs.models import Catalogs

from api.serializers import (
    MachineListSerializer, 
    MachineDetailSerializer,
    ManifestSerializer
)

import datetime
import json
import logging
import os
import mimetypes
import plistlib
import re
import base64
import bz2
import requests
import urllib

LOGGER = logging.getLogger('munkiwebadmin')

try:
    TIMEOUT = settings.TIMEOUT
except AttributeError:
    TIMEOUT = 20

def normalize_value_for_filtering(value):
    '''Converts value to a list of strings'''
    if isinstance(value, (int, float, bool, str, dict)):
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
            if ('date' in key.lower() and isinstance(value, str)
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


def convert_html_to_json(raw_html):
    LOGGER.debug("raw html: %s", raw_html)
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    try:
        data = json.loads(cleantext.strip())
    except (ValueError, KeyError, TypeError):
        data = ""
    return data


def model_lookup(serial):
    """Determines the models human readable description based off the serial
    number"""

    options = "page=categorydata&serialnumber=%s" % serial
    url = "https://km.support.apple.com/kb/index?%s" % options
    
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print("HTTP Error: %s" % e.code)
        return None
    
    try:
        data = response.read()
        model = json.loads(data.decode("utf-8"))
    except:
        print("Error: Could not decode JSON")
        return None
    return model


def get_device_img_url(serial):
    """ Returns the url to the device image for a given serial number"""
    model = model_lookup(serial)
    if model and model.get('id', None):
        url = "https://km.support.apple.com/kb/securedImage.jsp?productid=%s&size=240x240" % model['id']
    else:
        url = "https://support.apple.com/kb/securedImage.jsp?configcode=%s&size=240x240" % serial[-4:]
    return url


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
        response = requests.get(URL, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        pass
    else:
        if response.status_code in [200, 201, 202, 203, 204]:
            response.encoding = "utf-8-sig"
            return convert_html_to_json(response.text)
    return None


def postDataAPI(URL, postData):
    try:
        response = requests.post(URL, timeout=TIMEOUT, data=postData)
    except requests.exceptions.Timeout:
        pass
    else:
        if response.status_code in [200, 201, 202, 203, 204]:
            response.encoding = "utf-8-sig"
            return convert_html_to_json(response.text)
    return None

@csrf_exempt
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
            except FileDoesNotExistError as err:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': str(type(err)),
                                'detail': str(err)}),
                    content_type='application/json', status=404)
            except FileReadError as err:
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
            return HttpResponse(plistlib.dumps(response),
                                content_type='application/xml')

    if 'HTTP_X_METHODOVERRIDE' in request.META.keys():
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
                request_data = plistlib.loads(request.body)
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
        except FileAlreadyExistsError as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json',
                status=409)
        except FileWriteError as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        except FileError as err:
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
                    plistlib.dumps(request_data),
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
            request_data = plistlib.loads(request.body)
        if not request_data:
            # need to deal with this issue
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'NoRequestBody',
                            'detail':
                                'Request body was empty or missing valid data'}
                          ),
                content_type='application/json', status=400)
        try:
            LOGGER.debug("plist data %s", request_data)
            Plist.write(request_data, kind, filepath, request.user)
        except FileError as err:
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
                    plistlib.dumps(request_data),
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
            request_data = plistlib.loads(request.body)
        if not request_data:
            # need to deal with this issue
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'NoRequestBody',
                            'detail':
                                'Request body was empty or missing valid data'}
                          ),
                content_type='application/json', status=400)
        
        # read existing manifest
        plist_data = Plist.read(kind, filepath)
        plist_data.update(request_data)
        try:
            #data = plistlib.dumps(plist_data)
            Plist.write(plist_data, kind, filepath, request.user)
        except FileError as err:
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
                    plistlib.dumps(plist_data),
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
        except FileDoesNotExistError as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=404)
        except FileDeleteError as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        except FileError as err:
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
            except (IOError, OSError) as err:
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
                return HttpResponse(plistlib.dumps(response),
                                    content_type='application/xml')

    if 'HTTP_X_METHODOVERRIDE' in request.META.keys():
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
            filedata = request.body.decode('utf-8')
            if "data:image/png;base64" in filedata:
                img = filedata.split(',')[1]
                filedata = base64.b64decode(img)
        if not (filename and filedata):
            # malformed request
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'BadRequest',
                            'detail': 'Missing filename or filedata'}),
                content_type='application/json', status=400)
        try:
            if request.method == 'POST':
                LOGGER.debug("test")
                MunkiFile.new(kind, filedata, filename, request.user)
            else:
                MunkiFile.writedata(kind, filedata, filename, request.user)
        except (FileError, FileWriteError) as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        except Exception as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=500)
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
        except FileDoesNotExistError as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=404)
        except FileDeleteError as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        except FileError as err:
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)}),
                content_type='application/json', status=403)
        else:
            # success
            return HttpResponse(status=204)


class ReportsListAPIView(ListAPIView):
    permission_classes = [DjangoModelPermissions]

    queryset = Machine.objects.all()
    serializer_class = MachineListSerializer


class ReportsDetailAPIView(CreateModelMixin, DestroyModelMixin, UpdateModelMixin, RetrieveAPIView):
    permission_classes = [DjangoModelPermissions]
    
    queryset = Machine.objects.all()
    serializer_class = MachineDetailSerializer
    
    lookup_url_kwarg = "serial_number"
    pk_url_kwarg = "serial_number"

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    

class CatalogsListView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post']
    permission_classes = [DjangoModelPermissions]
    
    def get_queryset(self):
        try:
            response = Catalogs.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = Plist.list('catalogs')

        filter_terms = self.request.GET.copy()
        LOGGER.debug("filter_terms: %s", filter_terms)

        # remove the _ parameter
        if '_' in filter_terms.keys():
            del filter_terms['_']

        # remove the api_fields parameter
        api_fields = None
        if 'api_fields' in filter_terms.keys():
            api_fields = filter_terms['api_fields']
            del filter_terms['api_fields']

        response = []
        for item_name in queryset:
            LOGGER.debug("item_name: %s", item_name)
            plist = Plist.read('catalogs', item_name)
            plist = convert_dates_to_strings(plist)
            plist = {'contents': plist}
            plist['filename'] = item_name
            matches_filters = True
            for key, value in filter_terms.items():
                LOGGER.debug("key: %s, value: %s", key, value)
                LOGGER.debug("plist: %s", plist)
                if key not in plist:
                    LOGGER.debug("key not in plist")
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
                    LOGGER.debug("plist: %s", plist)
                response.append(plist)
        return response
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request):
        return Response(self.get_object())


class CatalogsDetailAPIView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post']
    permission_classes = [DjangoModelPermissions]
    
    def get_queryset(self):
        try:
            response = Catalogs.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = Plist.read('catalogs', self.kwargs['filepath'])
        queryset = convert_dates_to_strings(queryset)
        return queryset
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request, filepath):
        return Response(self.get_object())
    

class ManifestsListView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post']
    permission_classes = [DjangoModelPermissions]
    serializer_class = ManifestSerializer

    def get_queryset(self):
        try:
            items = Plist.list('manifests')
            response = ManifestFile.objects.all()
            response.values = items
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = self.get_queryset().values

        filter_terms = self.request.GET.copy()
        LOGGER.debug("filter_terms: %s", filter_terms)

        # remove the _ parameter
        if '_' in filter_terms.keys():
            del filter_terms['_']

        # remove the api_fields parameter
        api_fields = None
        if 'api_fields' in filter_terms.keys():
            api_fields = filter_terms['api_fields']
            del filter_terms['api_fields']

        response = []
        for item_name in queryset:
            LOGGER.debug("item_name: %s", item_name)
            plist = Plist.read('manifests', item_name)
            plist = convert_dates_to_strings(plist)
            plist['filename'] = item_name
            matches_filters = True
            for key, value in filter_terms.items():
                LOGGER.debug("key: %s, value: %s", key, value)
                LOGGER.debug("plist: %s", plist)
                if key not in plist:
                    LOGGER.debug("key not in plist")
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
                    LOGGER.debug("plist: %s", plist)
                response.append(plist)
        return response
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request):
        return Response(self.get_object())


class ManifestsDetailAPIView(GenericAPIView, ListModelMixin, CreateModelMixin, DestroyModelMixin, UpdateModelMixin):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    permission_classes = [DjangoModelPermissions]
    serializer_class = ManifestSerializer

    def get_queryset(self):
        try:
            response = ManifestFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = Plist.read('manifests', self.kwargs['filepath'])
        queryset = convert_dates_to_strings(queryset)
        filter_terms = self.request.GET.copy()

        # remove the _ parameter
        if '_' in filter_terms.keys():
            del filter_terms['_']

        # remove the api_fields parameter
        api_fields = None
        if 'api_fields' in filter_terms.keys():
            api_fields = filter_terms['api_fields']
            del filter_terms['api_fields']
        
        if api_fields:
            for key in list(queryset):
                if key not in api_fields:
                    del queryset[key]
        return queryset
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request, filepath):
        serializer = ManifestSerializer(self.get_object())
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        serializer = ManifestSerializer(data=request.data)
        if serializer.is_valid():
            Plist.new(serializer.data, "manifests", serializer.data['filepath'], request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400) 
    
    def put(self, request, *args, **kwargs):
        serializer = ManifestSerializer(data=request.data)
        if serializer.is_valid():
            Plist.write(serializer.data, "manifests", self.kwargs['filepath'], request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class PkgsinfoListView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post']
    permission_classes = [DjangoModelPermissions]
    
    def get_queryset(self):
        try:
            response = PkginfoFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = Plist.list('pkgsinfo')
        filter_terms = self.request.GET.copy()

        # remove the _ parameter
        if '_' in filter_terms.keys():
            del filter_terms['_']

        # remove the api_fields parameter
        api_fields = None
        if 'api_fields' in filter_terms.keys():
            api_fields = filter_terms['api_fields']
            del filter_terms['api_fields']

        response = []
        for item_name in queryset:
            LOGGER.debug("item_name: %s", item_name)
            plist = Plist.read('pkgsinfo', item_name)
            plist = convert_dates_to_strings(plist)
            plist['filename'] = item_name
            matches_filters = True
            for key, value in filter_terms.items():
                LOGGER.debug("key: %s, value: %s", key, value)
                LOGGER.debug("plist: %s", plist)
                if key not in plist:
                    LOGGER.debug("key not in plist")
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
                    LOGGER.debug("plist: %s", plist)
                response.append(plist)
        return response
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request):
        return Response(self.get_object())


class PkgsinfoDetailAPIView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post']
    permission_classes = [DjangoModelPermissions]
    
    def get_queryset(self):
        try:
            response = PkginfoFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = Plist.read('pkgsinfo', self.kwargs['filepath'])
        queryset = convert_dates_to_strings(queryset)
        filter_terms = self.request.GET.copy()

        api_fields = None
        if 'api_fields' in filter_terms.keys():
            api_fields = filter_terms['api_fields']
            del filter_terms['api_fields']
        
        if api_fields:
            for key in list(queryset):
                if key not in api_fields:
                    del queryset[key]
        return queryset
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request, filepath):
        return Response(self.get_object())


class PkgsListView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post']
    permission_classes = [DjangoModelPermissions]
    
    def get_queryset(self):
        try:
            response = PkginfoFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        return MunkiFile.list('pkgs')
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request):
        return Response(self.get_object())    


class PkgsDetailAPIView(GenericAPIView, ListModelMixin):
    http_method_names = ['get']
    permission_classes = [DjangoModelPermissions]
    
    def get_queryset(self):
        try:
            response = PkginfoFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        filepath = self.kwargs['filepath']
        fullpath = MunkiFile.get_fullpath('pkgs', filepath)
        if not os.path.exists(fullpath):
            return Response({'result': 'failed',
                            'exception_type': 'FileDoesNotExist',
                            'detail': '%s does not exist' % filepath})
        try:
            response = FileResponse(
                open(fullpath, 'rb'),
                content_type=mimetypes.guess_type(fullpath)[0])
            response['Content-Length'] = os.path.getsize(fullpath)
            response['Content-Disposition'] = (
                'attachment; filename="%s"' % os.path.basename(filepath))
            return response
        except (IOError, OSError) as err:
            return Response({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)})
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request, filepath):
        return self.get_object()


class IconsListView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post']
    permission_classes = [DjangoModelPermissions]
    
    def get_queryset(self):
        try:
            response = PkginfoFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        return MunkiFile.list('icons')
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request):
        return Response(self.get_object())


class IconsDetailAPIView(GenericAPIView, ListModelMixin):
    http_method_names = ['get']
    permission_classes = [DjangoModelPermissions]
    
    def get_queryset(self):
        try:
            response = PkginfoFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        filepath = self.kwargs['filepath']
        fullpath = MunkiFile.get_fullpath('icons', filepath)
        if not os.path.exists(fullpath):
            return Response({'result': 'failed',
                            'exception_type': 'FileDoesNotExist',
                            'detail': '%s does not exist' % filepath})
        try:
            response = FileResponse(
                open(fullpath, 'rb'),
                content_type=mimetypes.guess_type(fullpath)[0])
            response['Content-Length'] = os.path.getsize(fullpath)
            response['Content-Disposition'] = (
                'attachment; filename="%s"' % os.path.basename(filepath))
            return response
        except (IOError, OSError) as err:
            return Response({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)})
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request, filepath):
        return self.get_object()

