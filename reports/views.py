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

            if report_plist:
                time = report_plist.MachineInfo.SystemProfile[0].SPSoftwareDataType[0].uptime
                time = time[3:].split(':')

                disksPreList = []
                disksList = []
                counter = 0
                # Loops every partition in SPStorageDataType and generates a list with all the names of the disks
                for index, i in enumerate(report_plist.MachineInfo.SystemProfile[0].SPStorageDataType):
                    deviceName = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].physical_drive.device_name
                    partitionName = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index]._name
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
                    for index, b in enumerate(report_plist.MachineInfo.SystemProfile[0].SPStorageDataType):
                        # Reading Name of disk inside the partition-information
                        diskName = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].physical_drive.device_name
                        partitionName = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index]._name
                        # If diskName is equal to the actual iteration of disksPreList then the ifromation will be written into the values of the various dicts
                        if diskName == i:
                            # Reading partition information from system_profiler
                            partitionsAttributesDict = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index]
                            # Calculate how many percent are in use of the parttion and populates the key percentFull of the partition information
                            partitionsAttributesDict['percentFull'] = 100 * (float(report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].size_in_bytes - report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].free_space_in_bytes) / report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].size_in_bytes)
                            partitionDict['partitionName'] = partitionName
                            partitionDict['partitionAtributes'] = partitionsAttributesDict
                            partitionsList.append(partitionDict)
                            partitionDict = {}
                            # Calculate the diskSize by adding every parttion-size to diskSize
                            diskSize = diskSize + report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].size_in_bytes
                            diskInfoDict['physicalDisk'] = report_plist.MachineInfo.SystemProfile[0].SPStorageDataType[index].physical_drive
                    diskInfoDict['partitions'] = partitionsList
                    partitionsList = []
                    diskInfoDict['diskName'] = i
                    diskInfoDict['diskSize'] = diskSize
                    disksList.append(diskInfoDict)
                    diskSize = 0
                    partitionsDict = {}
                    diskInfoDict = {}

                context = {'machine': machine,
                           'report_plist': report_plist,
                           'disksList': disksList,
                           'time': time,
                           }
            else:
                context = {'machine': machine,
                       'report_plist': report_plist,
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
def getManifest(request, manifest_path):
    """ returns json manifest """
    LOGGER.debug("Got read request for %s", manifest_path)
    try:
        plist = Plist.read('manifests', manifest_path)
    except (FileDoesNotExistError, FileReadError), err:
        return HttpResponse(
            json.dumps({'result': 'failed',
                        'exception_type': str(type(err)),
                        'detail': str(err)}),
            content_type='application/json', status=404)

    return HttpResponse(json.dumps(plist),
                        content_type='application/json')

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
            requiredDict[software.name]['icon'] = software.icon
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

@login_required
def getStatus(request):
    serial = request.POST.getlist('serial')[0]
    item = request.POST.getlist('item')[0]
    if request.is_ajax() and serial and item:
        machine = None
        report_plist = None
        status = "set"
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist, err:
            pass

        if machine:
            try:
                report = MunkiReport.objects.get(machine=machine)
                report_plist = report.get_report()
            except MunkiReport.DoesNotExist:
                pass

        if report_plist:
            if "InstalledItems" in report_plist and item in report_plist.InstalledItems:
                status = "installed"

            return HttpResponse(json.dumps(status),
                            content_type='application/json')
    # no ajax
    return HttpResponse(
        json.dumps({'result': 'failed',
                    'exception_type': str(type(err)),
                    'detail': str(err)}),
        content_type='application/json', status=404)

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

def getSoftwareList(catalogs):
    """return a dict with all catalogs consolidated"""
    swDict = dict()
    for catalog in catalogs:
        catalog_items = Catalog.detail(catalog)
        for item in catalog_items:
            if item.name in swDict:
                if item.version > swDict[item.name].version and catalog in swDict[item.name].catalogs:
                    swDict[item.name] = item
            else:
                swDict[item.name] = item
    return swDict
