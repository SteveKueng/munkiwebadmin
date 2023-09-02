from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import Http404
#from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.conf import settings
from django import forms
from django.db.models import Q
from django.db.models import Count

import json

from .models import Inventory, InventoryItem
from reports.models import Machine


def inventory_hash(request, serial):
    sha256hash = ''
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
            inventory_meta = Inventory.objects.get(machine=machine)
            sha256hash = inventory_meta.sha256hash
        except (Machine.DoesNotExist, Inventory.DoesNotExist):
            pass
    else:
        raise Http404
    return HttpResponse(sha256hash)


@login_required
@permission_required('inventory.can_view_inventory', login_url='/login/')
def index(request):
    all_machines = Machine.objects.all()

    context = {'machines': all_machines,
                'user': request.user,
                'page': 'inventory'}
    return render(request, 'inventory/index.html', context=context)


@login_required
@permission_required('inventory.can_view_inventory', login_url='/login/')
def detail(request, serial):
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial_number=serial)
        except Machine.DoesNotExist:
            raise Http404
    else:
        raise Http404

    machine = None
    try:
        machine = Machine.objects.get(serial_number=serial)
    except Machine.DoesNotExist:
        pass
        
    inventory_items = machine.inventoryitem_set.all()
    
    context = {'machine': machine,
                'inventory_items': inventory_items,
                'user': request.user,
                'page': 'inventory'}
    return render(request, 'inventory/detail.html', context=context)


@login_required
@permission_required('inventory.can_view_inventory', login_url='/login/')
def items(request):
    name = request.GET.get('name')
    version = request.GET.get('version')
    bundleid = request.GET.get('bundleid')
    bundlename = request.GET.get('bundlename')
    path = request.GET.get('path')
    
    if name or bundleid or bundlename or path:
        item_detail = {}
        item_detail['name'] = name or bundleid or bundlename or path
        
        items = InventoryItem.objects.all()
        if name:
            items = items.filter(name__exact=name)
        if version:
            if version.endswith('*'):
                items = items.filter(
                    version__startswith=version[0:-1])
            else:
                items = items.filter(version__exact=version)
        if bundleid:
            items = items.filter(bundleid__exact=bundleid)
        if bundlename:
            items = items.filter(bundlename__exact=bundlename)
        if path:
            items = items.filter(path__exact=path)
    
        item_detail['instances'] = []
        for item in items:
            instance = {}
            instance['name'] = name
            instance['serial'] = item.machine.serial_number
            instance['hostname'] = item.machine.hostname
            instance['username'] = item.machine.username
            instance['version'] = item.version
            instance['bundleid'] = item.bundleid
            instance['bundlename'] = item.bundlename
            instance['path'] = item.path
            item_detail['instances'].append(instance)
        
        context = {'item_detail': item_detail,
                    'user': request.user,
                    'page': 'inventory'}
        return render(request, 'inventory/item_detail.html', context=context)
    else:
        context = {'user': request.user,
                    'page': 'inventory'}
        return render(request, 'inventory/items.html', context=context)


def items_json(request):
    inventory_items = InventoryItem.objects.values(
        'name', 'version').annotate(num_machines=Count('machine'))

    # build a dict so we can group by name
    inventory_dict = {}
    for item in inventory_items:
        name = item['name']
        version = item['version']
        machine_count = item['num_machines']
        if not name in inventory_dict:
            inventory_dict[name] = []
        inventory_dict[name].append({'version': version, 
                                     'count': machine_count})

    # convert to an array for use by DataTables
    rows = []
    for name, versions in inventory_dict.items():
        rows.append({'name': name,
                     'versions': versions})

    # send it back in JSON format
    return HttpResponse(json.dumps(rows), content_type='application/json')