# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.http import Http404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Count
from collections import OrderedDict
from django.shortcuts import render

from models import Machine, MunkiReport, BusinessUnit
from manifests.models import ManifestFile
from catalogs.models import Catalog
from api.models import Plist, FileDoesNotExistError, FileReadError

import base64
import bz2
import plistlib
import re
import urllib
import urllib2
from datetime import datetime, timedelta, date
from xml.etree import ElementTree
import fnmatch
import json
import logging
import os

LOGGER = logging.getLogger('munkiwebadmin')

# Configure URLLIB2 to use a proxy.
try:
    PROXY_ADDRESS = settings.PROXY_ADDRESS
except:
    PROXY_ADDRESS = ""

try:
    BUSINESS_UNITS_ENABLED = settings.BUSINESS_UNITS_ENABLED
except:
    BUSINESS_UNITS_ENABLED = False

try:
    IMAGR_CONFIG_URL = settings.IMAGR_CONFIG_URL
except:
    IMAGR_CONFIG_URL = ""

try:
    MUNKI_REPO_DIR = settings.MUNKI_REPO_DIR
except:
    MUNKI_REPO_DIR = False

proxies = {
    "http":  PROXY_ADDRESS,
    "https": PROXY_ADDRESS
}

if PROXY_ADDRESS:
    proxy = urllib2.ProxyHandler(proxies)
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)


def get_required():
    """ Retruns all catalog items with updates and requres in dict """
    requiredDict = dict()
    catalog_items = Catalog.detail('all')
    if catalog_items:
        # run get every catalog item
        for item in catalog_items:
            # if item has requres add them to requiredDict
            if "requires" in item:
                requiredDict[item.name] = {'requires': item.requires}
            # if item has update for, add it to the right item in requiredDict
            if "update_for" in item:
                for update in item.update_for:
                    if update in requiredDict:
                        if "updates" in requiredDict[update]:
                            requiredDict[update]["updates"].append(item.name)
                        else:
                            requiredDict[update]["updates"] = [item.name]
                    else:
                        requiredDict[update] = {'updates':[item.name]}
    return requiredDict
CATALOG_REQUIRED = get_required()
def getRequired(item):
    """Retruns array with required / update catalog items"""
    required = dict()
    if CATALOG_REQUIRED:
        if item in CATALOG_REQUIRED:
            if "requires" in CATALOG_REQUIRED[item]:
                for require in CATALOG_REQUIRED[item]["requires"]:
                    required["requires"] = {require : getRequired(require)}

            if "updates" in CATALOG_REQUIRED[item]:
                for update in CATALOG_REQUIRED[item]["updates"]:
                    required["updates"] = {update : getRequired(update)}
    return required

#CLIENT dict
CLIENT = dict()
#manifest key with will be showed
KEYS = ['managed_installs', 'managed_uninstalls', 'optional_installs']
def getSoftware(manifest_name):
    """Returns manifest item"""
    manifest_path = MUNKI_REPO_DIR+"/manifests/"+manifest_name
    try:
        plist = Plist.read('manifests', manifest_path)
    except (FileDoesNotExistError, FileReadError), err:
        plist = None
        pass

    if plist:
        for key in KEYS:
            if key in plist:
                for element in plist[key]:
                    item = {'name': element, 'manifest':manifest_name}
                    if key in CLIENT:
                        CLIENT[key].append(item)
                    else:
                        CLIENT[key] = [item]

                    required = getRequired(element)
                    if required:
                        CLIENT[key][-1].update(required)

        for manifest in plist.included_manifests:
            getSoftware(manifest)
    return CLIENT

@login_required
@permission_required('reports.can_view_reports', login_url='/login/')
def index(request, computer_serial=None):
    '''Returns computer list or detail'''
    if computer_serial and request.is_ajax():
        # return manifest detail
        if request.method == 'GET':
            LOGGER.debug("Got read request for %s", computer_serial)

            machine = None
            try:
                machine = Machine.objects.get(serial_number=computer_serial)
            except Machine.DoesNotExist, err:
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': str(type(err)),
                                'detail': str(err)}),
                    content_type='application/json', status=404)

            if machine:
                try:
                    report = MunkiReport.objects.get(machine=machine)
                    report_plist = report.get_report()
                except MunkiReport.DoesNotExist:
                    report_plist = None
                    pass
            # determine if the model description information should be shown
            try:
                MODEL_LOOKUP_ENABLED = settings.MODEL_LOOKUP_ENABLED
            except:
                MODEL_LOOKUP_ENABLED = False

            # additional_info
            additional_info = {}
            # If enabled lookup the model description
            if MODEL_LOOKUP_ENABLED and machine.serial_number:
                additional_info['model_description'] = \
                    model_description_lookup(machine.serial_number)

            # -- get CLIENT_MANIFEST option --
            manifest_name = machine.serial_number
            try:
                if settings.CLIENT_MANIFEST == "hostname":
                    manifest_name = machine.hostname
            except:
                pass
            #for key, value in report_plist["MachineInfo"]["SystemProfile"][0].iteritems():
            #    print key
            CLIENT.clear()
            plist = getSoftware(manifest_name)
            #print plist

            time = report_plist.MachineInfo.SystemProfile[0].SPSoftwareDataType[0].uptime

            time = time[3:].split(':')

            devicesDict = {}

            for index, i in enumerate(report_plist.MachineInfo.SystemProfile[0].SPStorageDataType):
                deviceName = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].physical_drive.device_name
                partitionName = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index]._name
                #print report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index]._name
                #print deviceName
                devicesDict[deviceName] = {}

            #print devicesDict
            partitionsDict = {}
            partitionsContentDict = {}
            for i in devicesDict:
                for index, b in enumerate(report_plist.MachineInfo.SystemProfile[0].SPStorageDataType):
                    deviceName = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].physical_drive.device_name
                    partitionName = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index]._name
                    if deviceName == i:
                        partitionsContentDict = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index]
                        print 100 * (float(report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].size_in_bytes - report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].free_space_in_bytes) / report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].size_in_bytes)
                        partitionsContentDict['percentFull'] = 100 * (float(report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].size_in_bytes - report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].free_space_in_bytes) / report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].size_in_bytes)
                        partitionsDict[partitionName] = partitionsContentDict
                        devicesDict[i] = partitionsDict
                partitionsDict = {}

            print devicesDict


            #for index, i in enumerate(report_plist.MachineInfo.SystemProfile[0].SPStorageDataType):



            #print drives


            context = {'machine': machine,
                       'plist_text': plist,
                       'report_plist': report_plist,
                       'additional_info': additional_info,
                       'devicesDict': devicesDict,
                       'time': time,
                       }
            return render(request, 'reports/detail.html', context=context)

        if request.method == 'POST':
            return HttpResponse(
                json.dumps({'result': 'failed',
                            'exception_type': 'MethodNotSupported',
                            'detail': 'POST/PUT/DELETE should use the API'}),
                content_type='application/json', status=404)

    # return list of available computers
    LOGGER.debug("Got index request for computers")

    show = request.GET.get('show')
    os_version = request.GET.get('os_version')
    model = request.GET.get('model')
    nameFilter = request.GET.get('nameFilter')
    typeFilter = request.GET.get('typeFilter')
    businessunit = request.GET.get('businessunit')
    unknown = request.GET.get('unknown')

    subpage = ""

    if BUSINESS_UNITS_ENABLED:
        business_units = get_objects_for_user(request.user, 'reports.can_view_businessunit')
        if unknown:
            reports = Machine.objects.filter(businessunit__isnull=True)
            subpage = "unknown"
        else:
            reports = Machine.objects.filter(businessunit__exact=business_units)
    else:
        reports = Machine.objects.all()

    if show is not None:
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        today = date.today()
        tomorrow = today + timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        three_months_ago = today - timedelta(days=90)

        if show == 'errors':
            reports = reports.filter(munkireport__errors__gt=0)
        elif show == 'warnings':
            reports = reports.filter(munkireport__warnings__gt=0)
        elif show == 'activity':
            reports = reports.filter(munkireport__activity__isnull=False)
        elif show == 'hour':
            reports = reports.filter(report_time__gte=hour_ago)
        elif show == 'today':
            reports = reports.filter(report_time__gte=today)
        elif show == 'week':
            reports = reports.filter(report_time__gte=week_ago)
        elif show == 'month':
            reports = reports.filter(report_time__gte=month_ago)
        elif show == 'notweek':
            reports = reports.filter(
                report_time__range=(month_ago, week_ago))
        elif show == 'notmonth':
            reports = reports.filter(
                report_time__range=(three_months_ago,
                                                   month_ago))
        elif show == 'notquarter':
            reports = reports.exclude(report_time__gte=three_months_ago)
        elif show == 'macbook':
            reports = reports.filter(machine_model__startswith="MacBook")
            subpage = "macbook"
        elif show == 'mac':
            reports = reports.exclude(machine_model__startswith="MacBook")
            reports = reports.exclude(machine_model__startswith="VMware")
            subpage = "mac"
        elif show == 'vm':
            reports = reports.filter(machine_model__startswith="VMware")
            subpage = "vm"

    if not subpage:
        subpage = "reports"

    if os_version is not None:
        reports = reports.filter(os_version__exact=os_version)

    if model is not None:
        reports = reports.filter(machine_model__exact=model)

    if nameFilter is not None:
        reports = reports.filter(hostname__startswith=nameFilter)

    if typeFilter is not None and model is None:
        reports = reports.filter(machine_model__contains=typeFilter)

    if businessunit is not None:
        reports = reports.filter(businessunit__exact=businessunit)
        subpage = businessunit

    context = {'reports': reports,
                'user': request.user,
                'page': 'reports',
                'subpage': subpage,}
    return render(request, 'reports/clienttable.html', context=context)


@login_required
@permission_required('reports.can_view_dashboard', login_url='/login/')
def dashboard(request):
    if BUSINESS_UNITS_ENABLED:
        business_units = get_objects_for_user(request.user, 'reports.can_view_businessunit')
        reports = MunkiReport.objects.filter(machine__businessunit__exact=business_units)
        machines = Machine.objects.filter(businessunit__exact=business_units)
    else:
        reports = MunkiReport.objects.all()
        machines = Machine.objects.all()

    munki = {}
    munki['errors'] = reports.filter(errors__gt=0).count()
    munki['warnings'] = reports.filter(warnings__gt=0).count()
    munki['activity'] = reports.filter(
                            activity__isnull=False).count()

    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)

    munki['checked_in_this_hour'] = machines.filter(
        munkireport__timestamp__gte=hour_ago).count()
    munki['checked_in_today'] = machines.filter(
        munkireport__timestamp__gte=today).count()
    munki['checked_in_past_week'] = machines.filter(
        munkireport__timestamp__gte=week_ago).count()

    munki['not_for_week'] = machines.filter(
        munkireport__timestamp__range=(month_ago, week_ago)).count()
    munki['not_for_month'] = machines.filter(
        munkireport__timestamp__range=(three_months_ago, month_ago)).count()
    munki['not_three_months'] = machines.exclude(
        munkireport__timestamp__gte=three_months_ago).count()

    # get counts of each os version
    os_info = machines.values(
                'os_version').annotate(count=Count('os_version')).order_by()

    # get counts of each machine_model type
    machine_info = machines.values(
                     'machine_model').annotate(
                       count=Count('machine_model')).order_by()

    c = RequestContext(request,{'munki': munki,
                                'os_info': os_info,
                                'machine_info': machine_info,
                                'user': request.user,
                                'page': 'dashboard'})

    c.update(csrf(request))
    return render_to_response('reports/dashboard.html', c)


@login_required
@permission_required('reports.can_view_reports', login_url='/login/')
def detail_pkg(request, serial, manifest_name):
    machine = None
    manifest = None
    install_items = None

    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            raise Http404
    else:
        raise Http404

    report_plist = {}
    if machine:
        try:
            report = MunkiReport.objects.get(machine=machine)
            report_plist = report.get_report()
        except MunkiReport.DoesNotExist:
            pass

    # get autocomplete data
    install_items = Manifest.getInstallItemNames(manifest_name)
    valid_install_items = (install_items['suggested'] +
                           install_items['updates'] +
                            install_items['with_version'])
    suggested_install_items = install_items['suggested']
    valid_catalogs = Catalog.list()
    valid_manifest_names = Manifest.list()
    autocomplete_data = json.dumps({
        'items': install_items['suggested'],
        'catalogs': valid_catalogs,
        'manifests': valid_manifest_names
    })

    # loop trought includet manifests as long as it have one
    includetManifests = dict()
    def get_addition_manifests(manifest):
        detailManifest = Manifest.read(manifest)
        includetManifests.update({manifest:detailManifest})
        if "included_manifests" in detailManifest:
            for includetManifest in detailManifest.included_manifests:
                get_addition_manifests(includetManifest)

    manifest = Manifest.read(manifest_name)
    sorted_Manifests = OrderedDict()
    sorted_Manifests[manifest_name] = manifest
    if "included_manifests" in manifest:
        for includetManifest in manifest.included_manifests:
            get_addition_manifests(includetManifest)
        sort_list = manifest.included_manifests

        for key in sort_list:
            sorted_Manifests[key] = includetManifests[key]

        key_list = includetManifests.keys()
        key_list.sort()
        for key in key_list:
            if key not in sorted_Manifests:
                sorted_Manifests[key] = includetManifests[key]

    # item_details -> list with software and details
    # true_items for check if a software is in catalog or not
    item_details = {}
    true_items = list()
    if "catalogs" in manifest:
        for catalog in manifest.catalogs:
            catalog_detail = Catalog.detail(catalog)
            if catalog_detail:
                for detail in reversed(catalog_detail):
                    if not detail.name in item_details:
                        item_details[detail.name] = detail
                        true_items.append(detail.name)
                        if "icon_name" in item_details[detail.name]:
                            icon = Catalog.get_icon(item_details[detail.name].icon_name)
                        else:
                            icon = Catalog.get_icon(detail.name)
                        item_details[detail.name].icon_name = icon

    ManagedInstallsDetail = OrderedDict()
    if report_plist.has_key("ManagedInstalls"):
        for item in report_plist.ManagedInstalls:
            ManagedInstallsDetail[item.name] = item


    # installs
    installs = OrderedDict()
    listed = list()
    installsTypes = ["managed_installs", "managed_uninstalls", "optional_installs"]
    for installsType in installsTypes:
        installs[installsType] = OrderedDict()

        for number, manifests in enumerate(sorted_Manifests):
            installs[installsType][manifests] = OrderedDict()

            if manifest:
                for index, item in enumerate(sorted_Manifests[manifests][installsType]):
                    listed.append(item)
                    if ManagedInstallsDetail.has_key(item):
                        installs[installsType][manifests][item] = ManagedInstallsDetail[item]

                    if item in true_items:
                        if installs[installsType].get(manifests, {}).has_key(item):
                            installs[installsType][manifests][item].update(item_details[item])
                        else:
                            installs[installsType][manifests][item] = item_details[item]

                        installs[installsType][manifests][item].update({"incatalog" : "True"})
                    else:
                        if installs[installsType].get(manifests, {}).has_key(item):
                            installs[installsType][manifests][item].update({"incatalog" : "False"})
                        else:
                            installs[installsType][manifests][item] = {'name' : item, "incatalog" : "False"}


    required = OrderedDict()
    for item in sorted(ManagedInstallsDetail.items(),key=lambda x: x[1]['display_name']):
        if not item[0] in listed:
            if item_details.has_key(item[0]):
                ManagedInstallsDetail[item[0]].icon_name = item_details[item[0]].icon_name
            else:
                ManagedInstallsDetail[item[0]].icon_name = "/static/img/PackageIcon.png"

            required[item[0]] = ManagedInstallsDetail[item[0]]


    # handle items that were installed during the most recent run
    install_results = {}
    for result in report_plist.get('InstallResults', []):
        nameAndVers = result['name'] + '-' + result['version']
        if result['status'] == 0:
            install_results[nameAndVers] = "installed"
        else:
            install_results[nameAndVers] = 'error'

    if install_results:
        for item in report_plist.get('ItemsToInstall', []):
            name = item.get('display_name', item['name'])
            nameAndVers = ('%s-%s'
                % (name, item['version_to_install']))
            item['install_result'] = install_results.get(
                nameAndVers, 'pending')

        for item in report_plist.get('ManagedInstalls', []):
            if 'version_to_install' in item:
                name = item.get('display_name', item['name'])
                nameAndVers = ('%s-%s'
                    % (name, item['version_to_install']))
                if install_results.get(nameAndVers) == 'installed':
                    item['installed'] = True

    # handle items that were removed during the most recent run
    # this is crappy. We should fix it in Munki.
    removal_results = {}

    if removal_results:
        for item in report_plist.get('ItemsToRemove', []):
            name = item.get('display_name', item['name'])
            item['install_result'] = removal_results.get(
                name, 'pending')
            if item['install_result'] == 'removed':
                if not 'RemovedItems' in report_plist:
                    report_plist['RemovedItems'] = [item['name']]
                elif not name in report_plist['RemovedItems']:
                    report_plist['RemovedItems'].append(item['name'])

    c = RequestContext(request,{'manifest_name': manifest_name,
                                'manifest': manifest,
                               'report': report_plist,
                               'installs': installs,
                               'autocomplete_data': autocomplete_data,
                               'required': required,
                               'valid_manifest_names': valid_manifest_names,
                               'valid_catalogs': valid_catalogs,
                               })
    c.update(csrf(request))
    return render_to_response('reports/detail_pkg.html',c)


@login_required
@permission_required('reports.can_view_reports', login_url='/login/')
def appleupdate(request, serial):
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            raise Http404
    else:
        raise Http404

    report_plist = {}
    if machine:
        try:
            report = MunkiReport.objects.get(machine=machine)
            report_plist = report.get_report()
        except MunkiReport.DoesNotExist:
            pass

    try:
        AppleUpdates = report_plist.AppleUpdates
    except:
        AppleUpdates = {}

    history = {}
    if 'SystemProfile' in report_plist.get('MachineInfo', []):
                for profile in report_plist['MachineInfo']['SystemProfile']:
                    if profile['_dataType'] == 'SPInstallHistoryDataType':
                        history = profile._items

    c = RequestContext(request,{'history': history,
                               'AppleUpdates': AppleUpdates,
                               'page': 'reports'})

    c.update(csrf(request))
    return render_to_response('reports/appleupdates.html', c)


@login_required
def staging(request, serial):
    if request.method == 'POST':
        submit = request.POST
        workflow = submit.get('workflow')
        runtype = submit.get('type')

        if serial:
            try:
                machine = Machine.objects.get(serial_number=serial)
            except Machine.DoesNotExist:
                machine = Machine(serial_number=serial)
        else:
            raise Http404

        if runtype == "save":
            if workflow == "no workflow":
                machine.imagr_workflow = ""
                machine.imagr_status = ""
                machine.imagr_message = ""
            else:
                machine.imagr_workflow = workflow
            machine.save()
            return HttpResponse("OK!")
        elif runtype == "load":
            imagr_status = machine.imagr_status
            imagr_message = machine.imagr_message

            c = RequestContext(request,{'imagr_status': imagr_status,
                                        'imagr_message': imagr_message
                                        })
            c.update(csrf(request))
            return render_to_response('reports/staging_status.html', c)
    else:
        machine = None
        if serial:
            try:
                machine = Machine.objects.get(serial_number=serial)
            except Machine.DoesNotExist:
                raise Http404
        else:
            raise Http404

        imagr_workflow = machine.imagr_workflow
        #imagr_target = machine.imagr_target

        error = None
        workflows = {}
        imagr_config_plist = ""

        if IMAGR_CONFIG_URL:
            try:
                config = urllib.urlopen(IMAGR_CONFIG_URL)
                imagr_config_plist = config.read()
                imagr_config_plist = plistlib.readPlistFromString(imagr_config_plist)
            except:
                error = "Can't reach server!"
        else:
            error = "Imagr URL not defined!"

        c = RequestContext(request,{'imagr_workflow': imagr_workflow,
                                   #'imagr_target': imagr_target,
                                   'workflows': workflows,
                                   'error': error,
                                   'imagr_config_plist': imagr_config_plist,
                                   'machine_serial': serial,
                                   'page': 'reports'})

        c.update(csrf(request))
        return render_to_response('reports/staging.html', c)


@login_required
@permission_required('reports.can_view_reports', login_url='/login/')
def machine_detail(request, serial):
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            raise Http404
    else:
        raise Http404

    report_plist = {}
    if machine:
        try:
            report = MunkiReport.objects.get(machine=machine)
            report_plist = report.get_report()
        except MunkiReport.DoesNotExist:
            pass


    SoftwareData = ""
    DisplaysData = ""
    NetworkData = ""
    SPStorageDataType = ""

    for profile in report_plist['MachineInfo']['SystemProfile']:
        if profile['_dataType'] == 'SPSoftwareDataType':
            SoftwareData = profile._items
        elif profile['_dataType'] == 'SPDisplaysDataType':
            DisplaysData = profile._items
        elif profile['_dataType'] == 'SPNetworkDataType':
            NetworkData = profile._items
        elif profile['_dataType'] == 'SPStorageDataType':
            SPStorageDataType = profile._items


    # convert forward slashes in manifest names to colons
    if 'ManifestName' in report_plist:
        report_plist['ManifestNameLink'] = report_plist['ManifestName'].replace('/', ':')

    # determine if the warranty lookup information should be shown
    try:
        WARRANTY_LOOKUP_ENABLED = settings.WARRANTY_LOOKUP_ENABLED
    except:
        WARRANTY_LOOKUP_ENABLED = False

    # Determine Manufacture Date
    additional_info = {}
    if WARRANTY_LOOKUP_ENABLED and machine.serial_number:
        additional_info['manufacture_date'] = \
            estimate_manufactured_date(machine.serial_number)


    return render_to_response('reports/detail_machine.html',
                              {'machine': machine,
                               'report': report_plist,
                               'user': request.user,
                               'SoftwareData': SoftwareData,
                               'DisplaysData': DisplaysData,
                               'NetworkData': NetworkData,
                               'SPStorageDataType': SPStorageDataType,
                               'additional_info': additional_info,
                               'warranty_lookup_enabled': WARRANTY_LOOKUP_ENABLED,
                               'page': 'reports'})

@login_required
@permission_required('reports.can_view_reports', login_url='/login/')
def raw(request, serial):
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            raise Http404
    else:
        raise Http404

    report_plist = {}
    if machine:
        try:
            report = MunkiReport.objects.get(machine=machine)
            report_plist = report.decode(report.report)
        except MunkiReport.DoesNotExist:
            pass

    return HttpResponse(plistlib.writePlistToString(report_plist),
        content_type='text/plain')

def imagr(request, serial):
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            raise Http404
    else:
        raise Http404

    imagr_infos = {}
    if machine.imagr_workflow:
        imagr_infos["workflow"] = machine.imagr_workflow
    imagr_infos["target"] = "firstDisk"
    #imagr_infos["target"] = machine.imagr_target

    return HttpResponse(plistlib.writePlistToString(imagr_infos),
        content_type='text/plain')

def getname(request, serial):
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            return HttpResponse("none",
                content_type='text/plain')
    else:
        raise Http404

    return HttpResponse(machine.hostname,
        content_type='text/plain')

def estimate_manufactured_date(serial):
    """Estimates the week the machine was manfactured based off it's serial
    number"""
    # See http://www.macrumors.com/2010/04/16/apple-tweaks-serial-number
    #      -format-with-new-macbook-pro/ for details about serial numbers
    if len(serial) == 11:
        try:
            year = serial[2]
            est_year = 2000 + '   3456789012'.index(year)
            week = serial[3:5]
            return formatted_manafactured_date(int(est_year), int(week))
        except:
            return 'Unknown'
    elif len(serial) == 12:
        try:
            year_code = 'cdfghjklmnpqrstvwxyz'
            year = serial[3].lower()
            est_year = 2010 + (year_code.index(year) / 2)
            est_half = year_code.index(year) % 2
            week_code = ' 123456789cdfghjklmnpqrtvwxy'
            week = serial[4:5].lower()
            est_week = week_code.index(week) + (est_half * 26)
            return formatted_manafactured_date(int(est_year), int(est_week))
        except:
            return 'Unknown'
    else:
        return 'Unknown'

def formatted_manafactured_date(year, week):
    """Converts the manufactured year and week number into a nice string"""
    # Based on accepted solution to this stackoverflow question
    # http://stackoverflow.com/questions/5882405/get-date-from-iso-week
    #  -number-in-python

    if not isinstance(year, int) or not isinstance(week, int):
        return 'Unknown'

    ret = datetime.strptime('%04d-%02d-1' % (year, week), '%Y-%W-%w')
    if date(year, 1, 4).isoweekday() > 4:
        ret -= timedelta(days=7)

    # Format Day
    day = ret.strftime('%d')
    if 4 <= int(day) <= 20 or 24 <= int(day) <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][int(day) % 10 - 1]

    # Build formatted date string
    formatted_date = 'Week of %s %s %s' % \
        (ret.strftime('%A'), day.lstrip('0') + suffix, ret.strftime('%B %Y'))
    return formatted_date

def warranty(request, serial):
    """Determines the warranty status of a machine, and it's expiry date"""
    # Based on: https://github.com/chilcote/warranty

    url = 'https://selfsolve.apple.com/wcResults.do'
    values = {'sn' : str(serial),
              'Continue' : 'Continue',
              'cn' : '',
              'locale' : '',
              'caller' : '',
              'num' : '0' }

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()

    match_obj = re.search( r'Repairs and Service Coverage: (.*)<br/>', \
                          the_page, re.M|re.I)
    if match_obj:
        if 'Active' in match_obj.group():
            match_obj = re.search( r'Estimated Expiration Date: (.*)<br/>', \
                                  match_obj.group(), re.M|re.I)
            if match_obj:
                expiry_date = match_obj.group().strip('<br/>')
                return HttpResponse('<span style="color:green">Active</span>'\
                    '<br/>%s<br/><a href="javascript:postwith(\'%s\',%s)">'\
                    'More Information</a>' % (expiry_date, url, values))
            else:
                return HttpResponse('<span style="color:green">Active</span>'\
                    '<br/><a href="javascript:postwith(\'%s\',%s)">'\
                    'More Information</a>' % (expiry_date, url, values))
        elif 'Expired' in match_obj.group():
            return HttpResponse('<span>Expired</span>'
                '<br/><a href="javascript:postwith(\'%s\',%s)">'\
                'More Information</a>' % (url, values))

        else:
            return HttpResponse('<span>Unknown Status: Try clicking '
                '<a href="javascript:postwith(\'%s\',%s)">here</a> to '
                'manually check' % (url, values))
    else:
        match_obj = re.search( r'RegisterProduct.do\?productRegister', \
                                  the_page, re.M|re.I)
        if match_obj:
            return HttpResponse('<span>Product Requires Validation<br/>'\
                'Click <a href="javascript:postwith(\'%s\',%s)">here</a> '\
                'for more information' % (url, values))
        else:
            return HttpResponse('<span>Unknown Status: Try clicking '\
                '<a href="javascript:postwith(\'%s\',%s)">here</a> to '\
                ' manually check' % (url, values))

def model_description_lookup(serial):
    """Determines the models human readable description based off the serial
    number"""
    # Based off https://github.com/MagerValp/MacModelShelf/

    snippet = serial[-3:]
    if (len(serial) == 12):
        snippet = serial[-4:]
    try:
        response = urllib2.urlopen(
            "http://support-sp.apple.com/sp/product?cc=%s&lang=en_US"
            % snippet, timeout=2)
        et = ElementTree.parse(response)
        return et.findtext("configCode").decode("utf-8")
    except:
        return ''

@login_required
@permission_required('reports.delete_machine')
def delete_machine(request, serial):
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            raise Http404
    else:
        raise Http404

    if machine:
        try:
            report = MunkiReport.objects.get(machine=machine)
            report.delete()
        except MunkiReport.DoesNotExist:
            pass

    machine.delete()
    return HttpResponse("Machine deleted\n")
