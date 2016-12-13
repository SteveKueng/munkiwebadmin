from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from process.models import Process

import json
import os
import logging
import re

from operator import itemgetter

try:
    BASE_DIR = settings.BASE_DIR
except:
	BASE_DIR = ""

if os.path.isdir(BASE_DIR + '/reposadolib'):
	from reposadolib import reposadocommon

LOGGER = logging.getLogger('munkiwebadmin')

@login_required
def status(request):
    	'''Returns status of long-running process'''
	LOGGER.debug('got status request for update_list_process')
	status_response = {}
	processes = Process.objects.filter(name='update_list_process')
	if processes:
		# display status from one of the active processes
		# (hopefully there is only one!)
		process = processes[0]
		status_response['statustext'] = process.statustext
	else:
		status_response['statustext'] = 'Processing'
	return HttpResponse(json.dumps(status_response),
						content_type='application/json')

def list_products(sort_order='date'):
	'''Prints a list of Software Update products'''

	def sort_by_key(a, b):
		"""Internal comparison function for use with sorting"""
		return cmp(a['sort_key'], b['sort_key'])

	sort_keys = {'date':  'PostDate',
                 'title': 'title',
                 'id':    'id'}

	sort_key = sort_keys.get(sort_order, 'PostDate')
	errormessages = []
	products = reposadocommon.getProductInfo()
	catalog_branches = reposadocommon.getCatalogBranches()
	product_list = []
	list_of_productids = products.keys()
	for productid in list_of_productids:
		if not productid in products:
			errormessages.append(
				'Skipped product %s because it does not exist '
				'in the ProductInfo database.' % productid)
			continue
		product_dict = {}
		product_dict['key'] = productid
		if sort_key == 'id':
			product_dict['sort_key'] = productid
		else:
			try:
				product_dict['sort_key'] = products[productid][sort_key]
			except KeyError:
				errormessages.append(
					'Product %s is missing the sort key %s -- '
					'Product info database may be incomplete'
					% (productid, sort_key))
				continue
		product_list.append(product_dict)
	product_list.sort(sort_by_key)
	product_item = []
	for product in product_list:
		if product['key'] in products:
			deprecation_state = False
			if not products[product['key']].get('AppleCatalogs'):
				# not in any Apple catalogs
				deprecation_state = True
			try:
				post_date = products[product['key']].get('PostDate').strftime('%Y-%m-%d')
			except BaseException:
				post_date = 'None'
			
			if products[product['key']].get('description', 'None'):
				description = re.findall('<body>(.*?)</body>', products[product['key']].get('description'), re.DOTALL)
			
			item = {'key': product['key'],
			'title': products[product['key']].get('title'),
			'version': products[product['key']].get('version'),
			'date': post_date,
			'depricated': deprecation_state,
			'description': description
			}
			
			if catalog_branches:
				for branch in catalog_branches.keys():
					if product['key'] in catalog_branches[branch]:
						item[branch] = '<input type="checkbox" id="'+product['key']+'_'+branch+'" checked/>'
					else:
						item[branch] = '<input type="checkbox" id="'+product['key']+'_'+branch+'" />'

			product_item.append(item)
	return product_item

@login_required
def index(request):
	if request.is_ajax():
		response = list_products()
		return HttpResponse(json.dumps(response),
                                content_type='application/json')
	
	catalog_branches = reposadocommon.getCatalogBranches().keys()
	context = {'branches': catalog_branches}
	return render(request, 'updates/updates.html', context=context)

@login_required
def dup_apple(branchname):
	catalog_branches = reposadocommon.getCatalogBranches()

	if branchname not in catalog_branches.keys():
		print 'No branch ' + branchname
		return jsonify(result=False)

	# generate list of (non-drepcated) updates
	products = reposadocommon.getProductInfo()
	prodlist = []
	for prodid in products.keys():
		if len(products[prodid].get('AppleCatalogs', [])) >= 1:
			prodlist.append(prodid)

	catalog_branches[branchname] = prodlist

	print 'Writing catalogs'
	reposadocommon.writeCatalogBranches(catalog_branches)
	reposadocommon.writeAllBranchCatalogs()

	return jsonify(result=True)

@login_required
def new_branch(request, branchname):
	catalog_branches = reposadocommon.getCatalogBranches()
	if branchname in catalog_branches:
		reposadocommon.print_stderr('Branch %s already exists!', branchname)
		return HttpResponse(
			json.dumps({'result': 'failed',
			'exception_type': 'Branch already exists!',
			'detail': 'Branch already exists!'}),
			content_type='application/json', status=404)
	catalog_branches[branchname] = []
	reposadocommon.writeCatalogBranches(catalog_branches)
	return HttpResponse("OK")

@login_required
def delete_branch(request, branchname):
    catalog_branches = reposadocommon.getCatalogBranches()
    if not branchname in catalog_branches:
        reposadocommon.print_stderr('Branch %s does not exist!', branchname)
        return

    del catalog_branches[branchname]

    # this is not in the common library, so we have to duplicate code
    # from repoutil
    for catalog_URL in reposadocommon.pref('AppleCatalogURLs'):
        localcatalogpath = reposadocommon.getLocalPathNameFromURL(catalog_URL)
        # now strip the '.sucatalog' bit from the name
        if localcatalogpath.endswith('.sucatalog'):
            localcatalogpath = localcatalogpath[0:-10]
        branchcatalogpath = localcatalogpath + '_' + branchname + '.sucatalog'
        if os.path.exists(branchcatalogpath):
            reposadocommon.print_stdout(
                'Removing %s', os.path.basename(branchcatalogpath))
            os.remove(branchcatalogpath)

    reposadocommon.writeCatalogBranches(catalog_branches)
    
    return HttpResponse("OK")

@login_required
def add_all(request, branchname):
	products = reposadocommon.getProductInfo()
	catalog_branches = reposadocommon.getCatalogBranches()
	
	catalog_branches[branchname] = products.keys()

	reposadocommon.writeCatalogBranches(catalog_branches)
	reposadocommon.writeAllBranchCatalogs()
	
	return HttpResponse("OK")

@login_required
def dup(request, frombranch, tobranch):
	catalog_branches = reposadocommon.getCatalogBranches()

	if frombranch not in catalog_branches.keys() or tobranch not in catalog_branches.keys():
		print 'No branch ' + branchname
		return jsonify(result=False)

	catalog_branches[tobranch] = catalog_branches[frombranch]

	print 'Writing catalogs'
	reposadocommon.writeCatalogBranches(catalog_branches)
	reposadocommon.writeAllBranchCatalogs()

	return HttpResponse("OK")

@login_required
def purge_product(request, product_ids="all-deprecated", force=False):
    '''Removes products from the ProductInfo.plist and purges their local 
    replicas (if they exist). Warns and skips if a product is not deprecated
    or is in any branch, unless force == True. If force == True, product is 
    also removed from all branches. This action is destructive and cannot be
    undone.
    product_ids is a list of productids.'''
    
    # sanity checking
    for item in product_ids:
        if item.startswith('-'):
            reposadocommon.print_stderr('Ambiguous parameters: can\'t tell if  '
                                     '%s is a parameter or an option!', item)
            return
    
    products = reposadocommon.getProductInfo()
    catalog_branches = reposadocommon.getCatalogBranches()
    downloaded_product_list = reposadocommon.getDownloadStatus()
    
    if 'all-deprecated' in product_ids:
        product_ids.remove('all-deprecated')
        deprecated_productids = [key for key in products.keys()
                                 if not products[key].get('AppleCatalogs')]
        product_ids.extend(deprecated_productids)
        
    # remove all duplicate product ids
    product_ids = list(set(product_ids))
    
    for product_id in product_ids:
        if not product_id in products:
            reposadocommon.print_stderr(
                'Product %s does not exist in the ProductInfo database. '
                'Skipping.', product_id)
            continue
        product = products[product_id]
        product_short_info = ('%s (%s-%s)' 
            % (product_id, product.get('title'), product.get('version')))
        if product.get('AppleCatalogs') and not force:
            reposadocommon.print_stderr(
                'WARNING: Product %s is in Apple catalogs:\n   %s',
                product_short_info, '\n   '.join(product['AppleCatalogs']))
            reposadocommon.print_stderr('Skipping product %s', product_id)
            continue
        branches_with_product = [branch for branch in catalog_branches.keys()
                                 if product_id in catalog_branches[branch]]
        if branches_with_product:
            if not force:
                reposadocommon.print_stderr(
                    'WARNING: Product %s is in catalog branches:\n    %s',
                    product_short_info, '\n    '.join(branches_with_product))
                reposadocommon.print_stderr('Skipping product %s', product_id)
                continue
            else:
                # remove product from all branches
                for branch_name in branches_with_product:
                    reposadocommon.print_stdout(
                        'Removing %s from branch %s...', 
                        product_short_info, branch_name)
                    catalog_branches[branch_name].remove(product_id)
                
        local_copy = getProductLocation(product, product_id)
        if local_copy:
            # remove local replica
            reposadocommon.print_stdout(
                'Removing replicated %s from %s...', 
                product_short_info, local_copy)
            try:
                shutil.rmtree(local_copy)
            except (OSError, IOError), err:
                reposadocommon.print_stderr(
                    'Error: %s', err)
                # but not fatal, so keep going...
        # delete product from ProductInfo database
        del products[product_id]
        # delete product from downloaded product list
        if product_id in downloaded_product_list:
            downloaded_product_list.remove(product_id)
        
    # write out changed catalog branches, productInfo,
    # and rebuild our local and branch catalogs
    reposadocommon.writeDownloadStatus(downloaded_product_list)
    reposadocommon.writeCatalogBranches(catalog_branches)
    reposadocommon.writeProductInfo(products)
    reposadocommon.writeAllLocalCatalogs()

    return HttpResponse("OK")


def datetime_handler(x):
	if isinstance(x, datetime.datetime):
		return x.isoformat()
	raise TypeError("Unknown type")

