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
from django.utils.datastructures import SortedDict

from tokenapi.decorators import token_required
from tokenapi.http import JsonResponse, JsonError

from models import Machine, MunkiReport, BusinessUnit
from manifests.models import Manifest
from catalogs.models import Catalog

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
import os

# Configure URLLIB2 to use a proxy. 
try:
    PROXY_ADDRESS = settings.PROXY_ADDRESS
except:
    PROXY_ADDRESS = ""

proxies = {
    "http":  PROXY_ADDRESS, 
    "https": PROXY_ADDRESS
}

if PROXY_ADDRESS:
    proxy = urllib2.ProxyHandler(proxies)
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)


@token_required
def submit(request, submission_type):
    if request.method != 'POST':
        raise Http404
    
    submit = request.POST
    serial = submit.get('serial')
    mac = submit.get('mac')
    client = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            machine = Machine(serial_number=serial)
    if machine:
        try:
            report = MunkiReport.objects.get(machine=machine)
        except MunkiReport.DoesNotExist:
            report = MunkiReport(machine=machine)
    
    if machine and report:
        machine.hostname = submit.get('name', '<NO NAME>')
        machine.remote_ip = request.META['REMOTE_ADDR']
        machine.last_munki_update = datetime.now()
        if 'username' in submit:
            machine.username = submit.get('username')
        if 'location' in submit:
            machine.location = submit.get('location')
        
        report.runtype = submit.get('runtype')
        report.timestamp = datetime.now()

        if submit.get('unit'):
            unit = BusinessUnit.objects.get(hash=submit.get('unit'))  
            machine.businessunit = unit

        if submission_type == 'postflight':
            report.runstate = u"done"
            if 'base64bz2report' in submit:
                report.update_report(submit.get('base64bz2report'))

            # extract machine data from the report
            report_data = report.get_report()
            if 'MachineInfo' in report_data:
                machine.os_version = report_data['MachineInfo'].get(
                    'os_vers', 'UNKNOWN')
                machine.cpu_arch = report_data['MachineInfo'].get(
                    'arch', 'UNKNOWN')
            machine.available_disk_space = \
                report_data.get('AvailableDiskSpace') or 0
            hwinfo = {}
            if 'SystemProfile' in report_data.get('MachineInfo', []):
                for profile in report_data['MachineInfo']['SystemProfile']:
                    if profile['_dataType'] == 'SPHardwareDataType':
                        hwinfo = profile._items[0]
                        break
            if hwinfo:
                machine.machine_model = hwinfo.get('machine_model') and hwinfo.get('machine_model') or u'unknown'
                machine.cpu_type = hwinfo.get('cpu_type') and hwinfo.get('cpu_type') or u'unknown'
                machine.cpu_speed = hwinfo.get('current_processor_speed') and hwinfo.get('current_processor_speed') or u'0'
                machine.ram = hwinfo.get('physical_memory') and hwinfo.get('physical_memory') or u'0'
                machine.mac = mac
           
            machine.save()
            report.save()
            return HttpResponse("Postflight report submmitted for %s.\n" 
                                 % submit.get('name'))
        
        if submission_type == 'preflight':
            report.runstate = u"in progress"
            report.activity = report.encode(
                {"Updating": "preflight"})
            machine.save()
            report.save()
            return HttpResponse(
                "Preflight report submmitted for %s.\n" %
                 submit.get('name'))
    
        if submission_type == 'report_broken_client':
            report.runstate = u"broken client"
            #report.report = None
            report.errors = 1
            report.warnings = 0
            machine.save()
            report.save()
            return HttpResponse(
                "Broken client report submmitted for %s.\n" %
                 submit.get('name'))

    return HttpResponse("No report submitted.\n")


@login_required
@permission_required('reports.can_view_reports', login_url='/login/')
def index(request):
    show = request.GET.get('show')
    os_version = request.GET.get('os_version')
    model = request.GET.get('model')
    nameFilter = request.GET.get('nameFilter')
    typeFilter = request.GET.get('typeFilter')
    businessunit = request.GET.get('businessunit')
    
    reports = MunkiReport.objects.all()
    subpage = ""

    if show is not None:
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        today = date.today()
        tomorrow = today + timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        three_months_ago = today - timedelta(days=90)
    
        if show == 'errors':
            reports = reports.filter(errors__gt=0)
        elif show == 'warnings':
            reports = reports.filter(warnings__gt=0)
        elif show == 'activity':
            reports = reports.filter(activity__isnull=False)
        elif show == 'hour':
            reports = reports.filter(machine__last_munki_update__gte=hour_ago)
        elif show == 'today':
            reports = reports.filter(machine__last_munki_update__gte=today)
        elif show == 'week':
            reports = reports.filter(machine__last_munki_update__gte=week_ago)
        elif show == 'month':
            reports = reports.filter(machine__last_munki_update__gte=month_ago)
        elif show == 'notweek':
            reports = reports.filter(
                machine__last_munki_update__range=(month_ago, week_ago))
        elif show == 'notmonth':
            reports = reports.filter(
                machine__last_munki_update__range=(three_months_ago,
                                                   month_ago))
        elif show == 'notquarter':
            reports = reports.exclude(machine__last_munki_update__gte=three_months_ago)
        elif show == 'macbook':
            reports = reports.filter(machine__machine_model__startswith="MacBook")
            subpage = "macbook"
        elif show == 'mac':
            reports = reports.exclude(machine__machine_model__startswith="MacBook")
            reports = reports.exclude(machine__machine_model__startswith="VMware")
            subpage = "mac"
        elif show == 'vm':
            reports = reports.filter(machine__machine_model__startswith="VMware")
            subpage = "vm"
    else:
        subpage = "reports"
        
    if os_version is not None:
        reports = reports.filter(machine__os_version__exact=os_version)
        
    if model is not None:
        reports = reports.filter(machine__machine_model__exact=model)
        
    if nameFilter is not None:
        reports = reports.filter(machine__hostname__startswith=nameFilter)
    
    if typeFilter is not None and model is None:
        reports = reports.filter(machine__machine_model__contains=typeFilter)

    if businessunit is not None:
        reports = reports.filter(machine__businessunit__exact=businessunit)
        subpage = businessunit

    hostnames = list()
    for report in reports:
        hostnames.append(report.machine.hostname)
    hostnames_json = json.dumps(hostnames)  

    c = RequestContext(request,{'reports': reports,
                                'user': request.user,
                                'hostnames': hostnames_json,
                                'page': 'reports',
                                'subpage': subpage,
                                })
    c.update(csrf(request))
    return render_to_response('reports/index.html', c)


@login_required
@permission_required('reports.can_view_dashboard', login_url='/login/')     
def dashboard(request):
    munki = {}
    munki['errors'] = MunkiReport.objects.filter(errors__gt=0).count()
    munki['warnings'] = MunkiReport.objects.filter(warnings__gt=0).count()
    munki['activity'] = MunkiReport.objects.filter(
                            activity__isnull=False).count()
                            
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)

    munki['checked_in_this_hour'] = Machine.objects.filter(
        last_munki_update__gte=hour_ago).count()
    munki['checked_in_today'] = Machine.objects.filter(
        last_munki_update__gte=today).count()
    munki['checked_in_past_week'] = Machine.objects.filter(
        last_munki_update__gte=week_ago).count()
    
    munki['not_for_week'] = Machine.objects.filter(
        last_munki_update__range=(month_ago, week_ago)).count()
    munki['not_for_month'] = Machine.objects.filter(
        last_munki_update__range=(three_months_ago, month_ago)).count()
    munki['not_three_months'] = Machine.objects.exclude(
        last_munki_update__gte=three_months_ago).count()
    
    # get counts of each os version
    os_info = Machine.objects.values(
                'os_version').annotate(count=Count('os_version')).order_by()
    
    # get counts of each machine_model type
    machine_info = Machine.objects.values(
                     'machine_model').annotate(
                       count=Count('machine_model')).order_by()
    
    # find machines with less than 5GB of available disk space
    low_disk_machines = Machine.objects.filter(
            available_disk_space__lt=5*2**20).values(
                'serial_number', 'hostname', 'available_disk_space')
    
    c = RequestContext(request,{'munki': munki,
                                'os_info': os_info,
                                'machine_info': machine_info,
                                'low_disk_machines': low_disk_machines,
                                'user': request.user,
                                'page': 'dashboard'})

    c.update(csrf(request))                  
    return render_to_response('reports/dashboard.html', c)


@login_required
@permission_required('reports.can_view_reports', login_url='/login/')
def detail(request, serial):
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            raise Http404
    else:
        raise Http404
    
    # get SSH option
    try:
        SSH_BUTTON_ENABLED = settings.SSH_BUTTON_ENABLED
    except:
        SSH_BUTTON_ENABLED = False

    # get VNC option
    try:
        VNC_BUTTON_ENABLED = settings.VNC_BUTTON_ENABLED
    except:
        VNC_BUTTON_ENABLED = False

    # determine if the model description information should be shown
    try:
        MODEL_LOOKUP_ENABLED = settings.MODEL_LOOKUP_ENABLED
    except:
        MODEL_LOOKUP_ENABLED = False

    # Determine Manufacture Date
    additional_info = {}
    # If enabled lookup the model description
    if MODEL_LOOKUP_ENABLED and machine.serial_number:
        additional_info['model_description'] = \
            model_description_lookup(machine.serial_number)

    # get CLIENT_MANIFEST option
    try:
        if settings.CLIENT_MANIFEST == "hostname":
            manifest_name = machine.hostname
        else:
            manifest_name = machine.serial_number
    except:
        manifest_name = machine.serial_number

    c = RequestContext(request,{'machine': machine,
                               'manifest_name': manifest_name,
                               'user': request.user,
                               'additional_info': additional_info,
                               'model_lookup_enabled': MODEL_LOOKUP_ENABLED,
                               'ssh_button_enabled': SSH_BUTTON_ENABLED,
                               'vnc_button_enabled': VNC_BUTTON_ENABLED,
                               'page': 'reports'})

    c.update(csrf(request))
    return render_to_response('reports/detail.html',c)

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
    sorted_Manifests = SortedDict()
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

    ManagedInstallsDetail = SortedDict()
    if report_plist.has_key("ManagedInstalls"):
        for item in report_plist.ManagedInstalls:
            ManagedInstallsDetail[item.name] = item


    # installs
    installs = SortedDict()
    listed = list()
    installsTypes = ["managed_installs", "managed_uninstalls", "optional_installs"]
    for installsType in installsTypes:
        installs[installsType] = SortedDict()
         
        for number, manifests in enumerate(sorted_Manifests):
            installs[installsType][manifests] = SortedDict()

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

                    #if installs[installsType][manifests].get(item, {}).has_key("requires"):
                     #   for require in installs[installsType][manifests][item].requires:
                      #      if not require in sorted_Manifests[manifests][installsType]:
                       #         sorted_Manifests[manifests][installsType].append(require)
                        #        if not require in update_requires:
                         #           update_requires.append(require)

                    #if installs[installsType][manifests].get(item, {}).has_key("update_for"):     
                     #   for update in installs[installsType][manifests][item].update_for:
                      #      if not update in sorted_Manifests[manifests][installsType]:
                       #         sorted_Manifests[manifests][installsType].append(update)
                        #        if not update in update_requires:
                         #           update_requires.append(update)


    required = SortedDict()
    for item in sorted(ManagedInstallsDetail.items(),key=lambda x: x[1]['display_name']):
        if not item[0] in listed:
            if item_details.has_key(item[0]):
                ManagedInstallsDetail[item[0]].icon_name = item_details[item[0]].icon_name
            else:
                ManagedInstallsDetail[item[0]].icon_name = "/static/img/PackageIcon.png"

            required[item[0]] = ManagedInstallsDetail[item[0]]

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
                    if profile['_dataType'] == 'SPNetworkDataType':
                        network = profile._items[1]

    c = RequestContext(request,{'history': history,
                               'AppleUpdates': AppleUpdates,
                               'page': 'reports'})

    c.update(csrf(request))
    return render_to_response('reports/appleupdates.html', c)


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
    for result in report_plist.get('RemovalResults', []):
        m = re.search('^Removal of (.+): (.+)$', result)
        if m:
            try:
                if m.group(2) == 'SUCCESSFUL':
                    removal_results[m.group(1)] = 'removed'
                else:
                    removal_results[m.group(1)] = m.group(2)
            except IndexError:
                pass
    
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
                
    if 'managed_uninstalls_list' in report_plist:
        report_plist['managed_uninstalls_list'].sort()

    return render_to_response('reports/detail_machine.html',
                              {'machine': machine,
                               'report': report_plist,
                               'user': request.user,
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
        mimetype='text/plain')

def lookup_ip(request):
    return HttpResponse(request.META['REMOTE_ADDR'], mimetype='text/plain')

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



