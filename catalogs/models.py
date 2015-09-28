import os
import plistlib

from django.conf import settings
from django.db import models

REPO_DIR = settings.MUNKI_REPO_DIR
STATIC_URL = settings.STATIC_URL
MEDIA_URL = settings.MEDIA_URL
ICONS_DIR = settings.ICONS_DIR
PROD_CATALOG = "production" # change this if your production catalog is different

class Catalog(object):
    @classmethod
    def list(self):
        '''Returns a list of available catalogs, which is a list
        of catalog names (strings)'''
        catalogs_path = os.path.join(REPO_DIR, 'catalogs')
        catalogs = []
        for name in os.listdir(catalogs_path):
            if name.startswith("._") or name == ".DS_Store":
                # don't process these
                continue
            try:
                catalog = plistlib.readPlist(os.path.join(catalogs_path, name))
            except Exception:
                # skip items that aren't valid plists
                pass
            else:
                catalogs.append(name)
        if not PROD_CATALOG in catalogs:
            catalogs.append(PROD_CATALOG)
        return catalogs
            
    
    @classmethod
    def detail(self, catalog_name):
        '''Gets the contents of a catalog, which is a list
        of pkginfo items'''
        catalog_path = os.path.join(
            REPO_DIR, 'catalogs', catalog_name)
        if os.path.exists(catalog_path):
            try:
                catalog_items = plistlib.readPlist(catalog_path)
                index = 0
                for item in catalog_items:
                    item['index'] = index
                    index += 1
                return catalog_items
            except Exception, errmsg:
                return None
        else:
            return None
                    
    
    @classmethod
    def item_detail(self, catalog_name, item_index):
        '''Returns detail for a single catalog item'''
        catalog_path = os.path.join(
            REPO_DIR, 'catalogs', catalog_name)
        if os.path.exists(catalog_path):
            try:
                catalog_items = plistlib.readPlist(catalog_path)
                return catalog_items[int(item_index)]
            except Exception, errmsg:
                return None
        else:
            return None


    @classmethod
    def getValidInstallItems(self, catalog_list):
        '''Returns a list of valid install item names for the
        list of catalogs'''
        install_items = set()
        for catalog in catalog_list:
            catalog_items = Catalog.detail(catalog)
            catalog_item_names = list(set(
                [item['name'] for item in catalog_items]))
            install_items.update(catalog_item_names)
            catalog_item_names_with_versions = list(set(
                [item['name'] + '-' + trimVersionString(item['version'])
                 for item in catalog_items]))
            install_items.update(catalog_item_names_with_versions)
        return list(install_items)

    @classmethod
    def get_icon(self, item_name):
        if not item_name.endswith(('.png', '.jpg', '.jpeg')):
            item_name = item_name + ".png"
        icons_path = os.path.join(os.path.join(REPO_DIR, ICONS_DIR), item_name)
        default_icon = STATIC_URL + 'img/PackageIcon.png'
        item_icon = MEDIA_URL + item_name
        if os.path.exists(icons_path):
            return item_icon
        else:
            return default_icon

class Catalogs(models.Model):
    class Meta:
            permissions = (("can_view_catalogs", "Can view catalogs"),)