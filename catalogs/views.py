from django.http import HttpResponse
from django.template import RequestContext
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from models import Catalog
from django.utils.datastructures import SortedDict

import json

def nameAndVersion(aString):
    ### from munkilib.updatecheck
    """Splits a string into the name and version number.

    Name and version must be seperated with a hyphen ('-')
    or double hyphen ('--').
    'TextWrangler-2.3b1' becomes ('TextWrangler', '2.3b1')
    'AdobePhotoshopCS3--11.2.1' becomes ('AdobePhotoshopCS3', '11.2.1')
    'MicrosoftOffice2008-12.2.1' becomes ('MicrosoftOffice2008', '12.2.1')
    """
    for delim in ('--', '-'):
        if aString.count(delim) > 0:
            chunks = aString.split(delim)
            vers = chunks.pop()
            name = delim.join(chunks)
            if vers[0] in '0123456789':
                return (name, vers)

    return (aString, '')
    
    
def trimVersionString(version_string):
    ### from munkilib.updatecheck
    """Trims all lone trailing zeros in the version string after major/minor.

    Examples:
      10.0.0.0 -> 10.0
      10.0.0.1 -> 10.0.0.1
      10.0.0-abc1 -> 10.0.0-abc1
      10.0.0-abc1.0 -> 10.0.0-abc1
    """
    if version_string == None or version_string == '':
        return ''
    version_parts = version_string.split('.')
    # strip off all trailing 0's in the version, while over 2 parts.
    while len(version_parts) > 2 and version_parts[-1] == '0':
        del(version_parts[-1])
    return '.'.join(version_parts)


@login_required                              
def item_detail(request, catalog_name, item_index):
    catalog_item = Catalog.item_detail(catalog_name, item_index)
    featured_keys = ['name', 'version', 'display_name', 
                     'description', 'catalogs', 'icon_name']
    
    # get icon
    if not "icon_name" in catalog_item:
        catalog_item["icon_name"] = ""

    # sort the item by key so keys are displayed
    # in expected order
    sorted_dict = SortedDict()
    for key in featured_keys:
        if key in catalog_item:
            sorted_dict[key] = catalog_item[key]
    key_list = catalog_item.keys()
    key_list.sort()
    for key in key_list:
        if key not in featured_keys:
            sorted_dict[key] = catalog_item[key]

    c = RequestContext(request,{'catalog_item': sorted_dict})
    c.update(csrf(request))
    return render_to_response('catalogs/item_detail.html', c)
                              

@login_required
def catalog_view(request, catalog_name=None, item_index=None):
    catalog_list = Catalog.list()
    if request.is_ajax():
        return HttpResponse(json.dumps(catalog_list),
                            mimetype='application/json')
    catalog = None
    catalog_item = None
    if not catalog_name:
        catalog_name = "all"

    catalog = Catalog.detail(catalog_name)

    catalog_items = list()
    for item in catalog:
        if 'display_name' not in item:
            item['display_name'] = item['name']
        if item.display_name not in catalog_items:
            catalog_items.append(item.display_name) 
    catalog_items_json = json.dumps(catalog_items)

    if item_index:
        catalog_item = Catalog.item_detail(catalog_name, item_index)

    # get icon
    counter = 0
    for item in catalog:
        if "icon_name" in item:
            icon = Catalog.get_icon(item.icon_name)
        else:
            icon = Catalog.get_icon(item.name)
        catalog[counter].icon_name = icon
        counter += 1

    c = RequestContext(request,{'catalog_list': catalog_list,
                                'catalog_name': catalog_name,
                                'catalog': catalog,
                                'item_index': item_index,
                                'catalog_item': catalog_item,
                                'catalog_items': catalog_items_json,
                                'user': request.user,
                                'page': 'catalogs'})
    c.update(csrf(request))
    return render_to_response('catalogs/catalog.html', c)