from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django import forms

from models import Packages
from catalogs.models import Catalog

import os

PROD_CATALOG = "production" # change this if your production catalog is different

@login_required
def index(request):
    if request.method == 'GET':
        findtext = request.GET.get('findtext')
        all_catalog_items = Packages.detail(findtext)
    else:
        all_catalog_items = Packages.detail()
    catalog_list = Catalog.list()
    catalog_name = 'none'
    if PROD_CATALOG in catalog_list:
        catalog_name = PROD_CATALOG
    elif 'testing' in catalog_list:
        catalog_name = 'testing'
    return render_to_response('pkgs/index.html',
                              {'user': request.user,
                               'all_catalog_items': all_catalog_items,
                               'catalog_list': catalog_list,
                               'catalog_name': catalog_name,
                               'findtext': findtext
                               })

@csrf_exempt
def confirm(request):
    if request.method == 'POST': # If the form has been submitted...
        dest_catalog = request.POST.get('dest_catalog')
        items_to_move = request.POST.getlist('items_to_move[]')
        tuple(items_to_move)
        for n,pkg in enumerate(items_to_move):
            pkg = pkg.split('___')
            items_to_move[n] = pkg
        c = {'user': request.user,
             'dest_catalog': dest_catalog,
             'items_to_move': items_to_move}
        return render_to_response('pkgs/confirm.html', c)
    else:
        return HttpResponse("No form submitted.\n")

@csrf_exempt
def done(request):
    if request.method == 'POST': # If the form has been submitted...
        final_items_to_move = request.POST.getlist('final_items_to_move[]')
        tuple(final_items_to_move)
        for n,pkg in enumerate(final_items_to_move):
            pkg = pkg.split('___')
            final_items_to_move[n] = pkg
        for pkg_name, pkg_version, pkg_catalog in final_items_to_move:
            Pkginfo.move(pkg_name, pkg_version, pkg_catalog)
        Packages.makecatalogs()
        context = {'user': request.user,
                   'final_items_to_move': final_items_to_move,
                   'done': 'Done'}
        return render_to_response('pkgs/done.html', context)
    else:
        return HttpResponse("No form submitted.\n")
