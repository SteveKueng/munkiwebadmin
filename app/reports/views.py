# -*- coding: utf-8 -*-
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Machine, MunkiReport
from catalogs.models import Catalog
from api.models import Plist, FileDoesNotExistError, FileReadError

import os
import plistlib
import urllib
from datetime import timedelta, date
import json
import logging

LOGGER = logging.getLogger('munkiwebadmin')

try:
    PROXY_ADDRESS = settings.PROXY_ADDRESS
except AttributeError:
    PROXY_ADDRESS = ""

try:
    DEFAULT_MANIFEST = settings.DEFAULT_MANIFEST
except AttributeError:
    DEFAULT_MANIFEST = "serial_number"

try:
    MUNKI_REPO_DIR = settings.MUNKI_REPO_DIR
except AttributeError:
    MUNKI_REPO_DIR = False
    
try:
    ICONS_URL = settings.ICONS_URL
except AttributeError:
    ICONS_URL = ""

try:
    VAULT_USERNAME = settings.VAULT_USERNAME
except AttributeError:
    VAULT_USERNAME = "admin"

proxies = {
    "http":  PROXY_ADDRESS,
    "https": PROXY_ADDRESS
}

if PROXY_ADDRESS:
    proxy = urllib.request.ProxyHandler(proxies)
    opener = urllib.request.build_opener(proxy)
    urllib.request.install_opener(opener)

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

@login_required
@permission_required('reports.can_view_reports', login_url='/login/')
def index(request, computer_serial=None):
    '''Returns computer list or detail'''
    if is_ajax(request):
        if computer_serial:
            # return manifest detail
            if request.method == 'GET':
                LOGGER.debug("Got read request for %s", computer_serial)
                machine = None
                try:
                    machine = Machine.objects.get(serial_number=computer_serial)
                except Machine.DoesNotExist as err:
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

                if report_plist:
                    try:
                        time = report_plist['MachineInfo']['SystemProfile'][0]['SPSoftwareDataType'][0]['uptime']
                        time = time[3:].split(':')
                    except Exception as err:
                        time = ""
                        pass

                    disksPreList = []
                    disksList = []
                    counter = 0
                    # Loops every partition in SPStorageDataType and generates a list with all the names of the disks
                    if "SPStorageDataType" in report_plist["MachineInfo"]["SystemProfile"][0]:
                        for index, i in enumerate(report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"]):
                            if "physical_drive" in report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]:
                                deviceName = report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["physical_drive"].get("device_name", None)
                            else:
                                deviceName = report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["com.apple.corestorage.pv"][0].get("device_name", None)
                            partitionName = report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["_name"]
                            # lops the already generated entrys in disksPreList and check it against the new value, to prevent doubbled entrys
                            for p in disksPreList:
                                if p == deviceName:
                                    counter = counter + 1
                            if counter == 0:
                                disksPreList.append(deviceName)
                            counter = 0

                    diskInfoDict = {}
                    partitionsList = []
                    partitionsAttributesDict = {}
                    partitionDict = {}
                    diskSize = 0

                    #Loops the before generated list of disks and extends the dicitionary with a partition-list and it's attributes
                    for i in disksPreList:
                        for index, b in enumerate(report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"]):
                            # Reading Name of disk inside the partition-information
                            if "physical_drive" in report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]:
                                diskName = report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["physical_drive"].get("device_name", None)
                            else:
                                diskName = report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["com.apple.corestorage.pv"][0].get("device_name", None)
                            partitionName = report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["_name"]
                            # If diskName is equal to the actual iteration of disksPreList then the ifromation will be written into the values of the various dicts
                            if diskName == i:
                                # Reading partition information from system_profiler
                                partitionsAttributesDict = report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]
                                # Calculate how many percent are in use of the parttion and populates the key percentFull of the partition information
                                partitionsAttributesDict['percentFull'] = 100 * (float(report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["size_in_bytes"] - report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["free_space_in_bytes"]) / report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["size_in_bytes"])
                                partitionDict['partitionName'] = partitionName
                                partitionDict['partitionAtributes'] = partitionsAttributesDict
                                partitionsList.append(partitionDict)
                                partitionDict = {}
                                # Calculate the diskSize by adding every parttion-size to diskSize
                                diskSize = diskSize + report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index]["size_in_bytes"]
                                diskInfoDict['physicalDisk'] = report_plist["MachineInfo"]["SystemProfile"][0]["SPStorageDataType"][index].get("physical_drive", None)
                        diskInfoDict['partitions'] = partitionsList
                        partitionsList = []
                        diskInfoDict['diskName'] = i
                        diskInfoDict['diskSize'] = diskSize
                        disksList.append(diskInfoDict)
                        diskSize = 0
                        partitionsDict = {}
                        diskInfoDict = {}

                    context = {'machine': machine,
                            'vault_username': VAULT_USERNAME,
                            'report_plist': report_plist,
                            'disksList': disksList,
                            'time': time,
                            'defaultManifest': DEFAULT_MANIFEST,
                            }
                else:
                    context = {'machine': machine,
                        'vault_username': VAULT_USERNAME,
                        'report_plist': report_plist,
                        'defaultManifest': DEFAULT_MANIFEST,
                        }

                return render(request, 'reports/detail.html', context=context)

            if request.method == 'POST':
                return HttpResponse(
                    json.dumps({'result': 'failed',
                                'exception_type': 'MethodNotSupported',
                                'detail': 'POST/PUT/DELETE should use the API'}),
                    content_type='application/json', status=404)
    
    # no ajax
    context = {'filterDevices': request.GET.urlencode(),
    'page': 'reports',
    'defaultManifestType': DEFAULT_MANIFEST,}
    return render(request, 'reports/index.html', context=context)

@login_required
@permission_required('reports.can_view_dashboard', login_url='/login/')
def dashboard(request):
    reports = MunkiReport.objects.all()
    machines = Machine.objects.all()

    munki = {}
    munki['errors'] = reports.filter(errors__gt=0).count()
    munki['warnings'] = reports.filter(warnings__gt=0).count()
    munki['activity'] = reports.filter(activity__isnull=False).count()

    now = timezone.now()
    hour_ago = now - timedelta(hours=1)
    today = now.date()
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

    context = { 'munki': munki,
                'os_info': os_info,
                'machine_info': machine_info,
                'user': request.user,
                'page': 'dashboard'}

    return render(request, 'reports/dashboard.html', context=context)

@login_required
def getjson(request):
    """ returns json list of machines """
    LOGGER.debug("Got json request for machines")
    machines = Machine.objects.all()
    return HttpResponse(json.dumps(list(machines.values())),
                            content_type='application/json')

@login_required
def getManifest(request, manifest_path):
    """ returns json manifest """
    LOGGER.debug("Got read request for %s", manifest_path)
    try:
        plist = Plist.read('manifests', manifest_path)
    except (FileDoesNotExistError, FileReadError) as err:
        return HttpResponse(
            json.dumps({'result': 'failed',
                        'exception_type': str(type(err)),
                        'detail': str(err)}),
            content_type='application/json', status=404)

    return HttpResponse(json.dumps(plist),
                        content_type='application/json')

@csrf_exempt
@login_required
def createRequired(request):
    """ returns catalog as json """
    catalogList = request.POST.getlist('catalogList[]')
    softwareList = getSoftwareList(catalogList)
    requiredDict = dict()
    for software in softwareList:
        software = softwareList[software]
        if software.name in requiredDict:
            requiredDict[software.name]['version'] = software.version
        else:
            requiredDict[software.name] = {'version': software.version}
        if "icon" in software:
            requiredDict[software.name]['icon'] = ICONS_URL + "/" + software.icon
        else:
            requiredDict[software.name]['icon'] = ICONS_URL + "/" + software.name + ".png"
        if "display_name" in software:
            requiredDict[software.name]['display_name'] = software.display_name
        # if software has requres add them to requiredDict
        if "requires" in software:
            requiredDict[software.name]['requires'] = software.requires
        # if software has update for, add it to the right software in requiredDict
        if "update_for" in software:
            for update in software.update_for:
                if update in requiredDict:
                    if "updates" in requiredDict[update]:
                        requiredDict[update]["updates"].append(software.name)
                    else:
                        requiredDict[update]["updates"] = [software.name]
                else:
                    requiredDict[update] = {'updates':[software.name]}
    return HttpResponse(json.dumps(requiredDict),
                        content_type='application/json')

@csrf_exempt
@login_required
def getStatus(request):
    serial = request.POST.getlist('serial')[0]
    item = request.POST.getlist('item')[0]
    if is_ajax(request) and serial and item:
        machine = None
        report_plist = None
        status = "led-grey"
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist as err:
            pass

        if machine:
            try:
                report = MunkiReport.objects.get(machine=machine)
                report_plist = report.get_report()
            except MunkiReport.DoesNotExist:
                pass

        if report_plist:
            if "InstalledItems" in report_plist and item in report_plist.InstalledItems:
                status = "led-green"
            elif "RemovedItems" in report_plist and item in report_plist.RemovedItems:
                status = "led-red"
            elif "ItemsToInstall" in report_plist:
                for itemToInstall in report_plist.ItemsToInstall:
                    if itemToInstall.name == item:
                        status = "led-orange"
            elif "ItemsToRemove" in report_plist:
                for itemToRemove in report_plist.ItemsToRemove:
                    if itemToRemove.name == item:
                        status = "led-orange"

            return HttpResponse(json.dumps(status),
                            content_type='application/json')
        else:
            return HttpResponse(status=200)
    # no ajax
    return HttpResponse(
        json.dumps({'result': 'failed',
                    'exception_type': "",
                    'detail': ""}),
        content_type='application/json', status=404)

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

def getSoftwareList(catalogs):
    """return a dict with all catalogs consolidated"""
    swDict = dict()
    for catalog in catalogs:
        catalog_items = Catalog.detail(catalog)
        if catalog_items:
            for item in catalog_items:
                if item.name in swDict:
                    if item.version > swDict[item.name].version and catalog in swDict[item.name].catalogs:
                        swDict[item.name] = item
                else:
                    swDict[item.name] = item
    return swDict

def downloadMunkiScripts(request):
    munkiscirpt_file = None
    munkiscript_path = settings.MUNKISCRIPTS_PATH
    for file in os.listdir(munkiscript_path):
        if file.endswith(".pkg"):
            munkiscirpt_file = os.path.join(munkiscript_path, file)
            break

    if munkiscirpt_file and os.path.exists(munkiscirpt_file):
        with open(munkiscirpt_file, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(munkiscirpt_file)
            return response
    raise Http404