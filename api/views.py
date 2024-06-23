"""
api/views.py
"""
from rest_framework.parsers import JSONParser, BaseParser
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from rest_framework.mixins import (
    CreateModelMixin, 
    DestroyModelMixin,
    UpdateModelMixin,
    ListModelMixin
)
from rest_framework.permissions import DjangoModelPermissions

from django.http import FileResponse
from django.conf import settings

from api.models import MunkiRepo
from api.models import FileReadError, \
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
import re
import base64
import bz2
import urllib
import sys
import io

LOGGER = logging.getLogger('munkiwebadmin')
MUNKITOOLS_DIR = settings.MUNKITOOLS_DIR

# import munkitools
sys.path.append(MUNKITOOLS_DIR)

try:
    from munkilib.wrappers import (readPlistFromString,
                                PlistReadError)
except ImportError:
    LOGGER.error('Failed to import munkilib')
    raise

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


class PlistXMLParser(BaseParser):
    """
    Plist xml parser.
    """
    media_type = 'application/xml'

    def parse(self, stream, media_type=None, parser_context=None):
        stream = stream.read()
        try:
            return readPlistFromString(stream)
        except PlistReadError as err:
            LOGGER.error('Error reading plist: %s', err)
            raise FileReadError(err)

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
        queryset = MunkiRepo.list('catalogs')

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
            plist = MunkiRepo.read('catalogs', item_name)
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
        queryset = MunkiRepo.read('catalogs', self.kwargs['filepath'])
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
    parser_classes = [PlistXMLParser, JSONParser]

    def get_queryset(self):
        try:
            items = MunkiRepo.list('manifests')
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
            plist = MunkiRepo.read('manifests', item_name)
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
    parser_classes = [PlistXMLParser, JSONParser]

    def get_queryset(self):
        try:
            response = ManifestFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = MunkiRepo.read('manifests', self.kwargs['filepath'])
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
            MunkiRepo.write(serializer.data, "manifests", kwargs['filepath'])
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400) 
    
    def put(self, request, *args, **kwargs):
        serializer = ManifestSerializer(data=request.data)
        if serializer.is_valid():
            MunkiRepo.write(serializer.data, "manifests", kwargs['filepath'])
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    def delete(self, request, *args, **kwargs):
        try:
            MunkiRepo.delete('manifests', kwargs['filepath'])
            return Response(status=204)
        except FileDeleteError as err:
            return Response({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)})


class PkgsinfoListView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post']
    permission_classes = [DjangoModelPermissions]
    parser_classes = [PlistXMLParser, JSONParser]
    
    def get_queryset(self):
        try:
            response = PkginfoFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = MunkiRepo.list('pkgsinfo')
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
            plist = MunkiRepo.read('pkgsinfo', item_name)
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
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    permission_classes = [DjangoModelPermissions]
    parser_classes = [PlistXMLParser, JSONParser]
    
    def get_queryset(self):
        try:
            response = PkginfoFile.objects.all()
        except FileDoesNotExistError as err:
            return Response({})
        except FileReadError as err:
            return Response({})
        return response
    
    def get_object(self):
        queryset = MunkiRepo.read('pkgsinfo', self.kwargs['filepath'])
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
    
    def post(self, request, *args, **kwargs):
        if request.data:
            MunkiRepo.write(request.data, "pkgsinfo", kwargs['filepath'])
            return Response({}, status=201)
        return Response({}, status=400)

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        if kwargs.get('deletePkg', False):
            try:
                MunkiRepo.delete('pkgs', kwargs['installer_item_location'])
            except FileDeleteError as err:
                return Response({'result': 'failed',
                                'exception_type': str(type(err)),
                                'detail': str(err)})

        try:
            MunkiRepo.delete('pkgsinfo', kwargs['filepath'])
            return Response(status=204)
        except FileDeleteError as err:
            return Response({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)})


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
        return MunkiRepo.list('pkgs')
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request):
        return Response(self.get_object())    


class PkgsDetailAPIView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'delete']
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
        item = MunkiRepo.get('pkgs', filepath)
        
        try:
            response = FileResponse(
                item,
                content_type=mimetypes.guess_type(item)[0])
            response['Content-Length'] = os.path.getsize(item)
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
    
    def delete(self, request, *args, **kwargs):
        print(kwargs)
        try:
            MunkiRepo.delete('pkgs', kwargs['filepath'])
            return Response(status=204)
        except FileDeleteError as err:
            return Response({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)})


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
        return MunkiRepo.list('icons')
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request):
        return Response(self.get_object())


class IconsDetailAPIView(GenericAPIView, ListModelMixin):
    http_method_names = ['get', 'post', 'put', 'delete']
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
        item = MunkiRepo.get('icons', filepath)
        buffer = io.BytesIO(item)
        buffer.seek(0)

        try:
            response = FileResponse(
                buffer,
                content_type=mimetypes.guess_type(filepath)[0],
                filename=filepath)
            return response
        except (IOError, OSError) as err:
            return Response({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)})
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request, filepath):
        return self.get_object()
    
    def post(self, request, *args, **kwargs):
        if request.data:
            imgBase64 = request.data['img'].split(',')[1].replace(" ", "+")
            img = base64.b64decode(imgBase64)

            MunkiRepo.writedata(img, "icons", kwargs['filepath'])
            return Response({}, status=201)
        return Response({}, status=400)
    
    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            MunkiRepo.delete('icons', kwargs['filepath'])
            return Response(status=204)
        except FileDeleteError as err:
            return Response({'result': 'failed',
                            'exception_type': str(type(err)),
                            'detail': str(err)})

