#from django.db import models
import os
import sys
import logging
import shutil
import subprocess
import plistlib
import optparse
import fnmatch

from django.conf import settings
from django.db import models

REPO_DIR = settings.MUNKI_REPO_DIR
STATIC_URL = settings.STATIC_URL
MEDIA_URL = settings.MEDIA_URL
ICONS_DIR = settings.ICONS_DIR
APPNAME = settings.APPNAME
DEFAULT_MAKECATALOGS = settings.DEFAULT_MAKECATALOGS
GIT = settings.GIT_PATH

usage = "%prog [options]"
o = optparse.OptionParser(usage=usage)
o.add_option("--makecatalogs", default=DEFAULT_MAKECATALOGS,
    help=("Path to makecatalogs. Defaults to '%s'. "
              % DEFAULT_MAKECATALOGS))

opts, args = o.parse_args()
MAKECATALOGS = opts.makecatalogs

def execute(command):
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        print(line) # yield line

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

    @classmethod
    def makecatalogs(self, committer):
        task = execute([MAKECATALOGS, REPO_DIR])
        if GIT:
            git = MunkiPkgGit()
            git.addMakeCatalogsForCommitter(committer)
        return True


    @classmethod
    def move_pkg(self, pkg_name, pkg_version, pkg_catalog, committer):
        '''Rewrites the catalog of the selected pkginfo files. Adapted from grahamgilbert/munki-trello'''
        done = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                # Try, because it's conceivable there's a broken / non plist
                plist = None
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    plist['catalogs'] = [pkg_catalog]
                    plistlib.writePlist(plist, os.path.join(root, name))
                    if GIT:
                        git = MunkiPkgGit()
                        git.addFileAtPathForCommitter(os.path.join(root, name), committer)
                    done = True
                    break
            if done:
                break
        return done

    @classmethod
    def add_catalog(self, pkg_name, pkg_version, pkg_orig, pkg_catalog, committer):
        '''Appends the catalog of the selected pkginfo files.'''
        done = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                plist = None
                # Try, because it's conceivable there's a broken / non plist
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    # Check that the catalog is not already in this plist
                    if pkg_catalog not in plist['catalogs']:
                        plist['catalogs'].append(pkg_catalog)
                        plistlib.writePlist(plist, os.path.join(root, name))
                        if GIT:
                            git = MunkiPkgGit()
                            git.addFileAtPathForCommitter(os.path.join(root, name), committer)
                    done = True
                    break
            if done:
                break

    @classmethod
    def remove_catalog(self, pkg_name, pkg_version, pkg_orig, committer):
        '''Removes the selected catalog from the pkginfo files.'''
        done = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                # Try, because it's conceivable there's a broken / non plist
                plist = None
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    current_catalogs = plist['catalogs']
                    # Try to remove this catalog from the array if it exists
                    try:
                        plist['catalogs'].remove(pkg_orig)
                    except:
                        pass
                    plistlib.writePlist(plist, os.path.join(root, name))
                    if GIT:
                        git = MunkiPkgGit()
                        git.addFileAtPathForCommitter(os.path.join(root, name), committer)
                    done = True
                    break
            if done:
                break

    @classmethod
    def delete_pkgs(self, pkg_name, pkg_version, committer):
        '''Deletes a package and its associated pkginfo file, then induces makecatalogs'''
        logger.info("pkg_name: %s; pkg_version: %s" % (pkg_name, pkg_version))
        done_delete = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                # Try, because it's conceivable there's a broken / non plist
                plist = None
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    pkg_to_delete = plist['installer_item_location']
                    if not GIT:
                        try:
                            os.remove(os.path.join(root, name))
                        except OSError as e:
                            logger.info("This failed to delete: %s" % (name))
                        try:
                            os.remove(os.path.join(REPO_DIR,'pkgs',pkg_to_delete))
                        except OSError as e:
                            logger.info("This failed to delete: %s" % (name))
                    else:
                        git = MunkiPkgGit()
                        git.deleteFileAtPathForCommitter(
                                os.path.join(root, name), committer)
                        if settings.GIT_IGNORE_PKGS:
                            try:
                                os.remove(os.path.join(REPO_DIR,'pkgs',pkg_to_delete))
                            except OSError as e:
                                logger.info("This failed to delete: %s" % (name))
                        else:
                            git.deleteFileAtPathForCommitter(
                                    os.path.join(REPO_DIR,'pkgs',pkg_to_delete), committer)
                    done_delete = True
                    break
            if done_delete:
                break

    @classmethod
    def save_pkginfo(self, pkg_name, pkg_version, pkg_info, committer):
        '''writes pkginfo'''
        done = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                plist = None
                # Try, because it's conceivable there's a broken / non plist
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    for key in pkg_info:
                        if pkg_info[key]:
                            plist[key] = pkg_info[key]
                        else:
                            try:
                                del plist[key]
                            except KeyError:
                                pass

                    plistlib.writePlist(plist, os.path.join(root, name))
                    if GIT:
                        git = MunkiPkgGit()
                        git.addFileAtPathForCommitter(os.path.join(root, name), committer)

                    done = True
                    break
            if done:
                break

class Catalogs(models.Model):
    class Meta:
            permissions = (("can_view_catalogs", "Can view catalogs"),)




#--------------------------

class MunkiPkgGit:
    """A simple interface for some common interactions with the git binary"""
    cmd = GIT
    args = []
    results = {}

    @staticmethod
    def __chdirToMatchPath(aPath):
        """Changes the current working directory to the same parent directory as
        the file specified in aPath. Example:
        "/Users/Shared/munki_repo/pkgsinfo/app/FredsApp-1.0.0.plist" would change
        directories to "/Users/Shared/munki_repo/pkgsinfo/app" """
        os.chdir(os.path.dirname(aPath))

    def runGit(self, customArgs=None):
        """Executes the git command with the current set of arguments and
        returns a dictionary with the keys 'output', 'error', and
        'returncode'. You can optionally pass an array into customArgs to
        override the self.args value without overwriting them."""
        customArgs = self.args if customArgs == None else customArgs
        proc = subprocess.Popen([self.cmd] + customArgs,
                                shell=False,
                                bufsize=-1,
                                stdin = subprocess.PIPE,
                                stdout = subprocess.PIPE,
                                stderr = subprocess.PIPE)
        (output, error) = proc.communicate()
        self.results = {"output": output,
                       "error": error, "returncode": proc.returncode}
        return self.results

    def pathIsRepo(self, aPath):
        """Returns True if the path is in a Git repo, false otherwise."""
        self.__chdirToMatchPath(aPath)
        self.runGit(['status', aPath])
        return self.results['returncode'] == 0

    def commitFileAtPathForCommitter(self, aPath, committer):
        """Commits the file at 'aPath'. This method will also automatically
        generate the commit log appropriate for the status of aPath where status
        would be 'modified', 'new file', or 'deleted'"""
        self.__chdirToMatchPath(aPath)
        # get the author information
        author_name = committer.first_name + ' ' + committer.last_name
        author_name = author_name if author_name != ' ' else committer.username
        author_email = (committer.email or
                        "%s@munkiwebadmin" % committer.username)
        # author_info = '%s <%s>' % (author_name, author_email)
        self.runGit(['config', 'user.email', author_email])
        self.runGit(['config', 'user.name', author_name])

        # get the status of the file at aPath
        statusResults = self.runGit(['status', aPath])
        statusOutput = statusResults['output']
        if statusOutput.find("new file:") != -1:
            action = 'created'
        elif statusOutput.find("modified:") != -1:
            action = 'modified'
        elif statusOutput.find("deleted:") != -1:
            action = 'deleted'
        else:
            action = 'did something with'

        # determine the path relative to REPO_DIR for the file at aPath
        pkgsinfo_path = os.path.join(REPO_DIR, 'pkgsinfo')
        itempath = aPath
        if aPath.startswith(pkgsinfo_path):
            itempath = aPath[len(pkgsinfo_path):]

        # generate the log message - would be good to pass details of each file
        # maybe we can get it from the status message - return it to views.py?
        # In the meantime, we just log the author and that it's a Munki-Do run
        # log_msg = ('%s %s pkginfo file \'%s\' via %s'
        #            % (author_name, action, itempath, APPNAME))
        log_msg = ('makecatalogs run by %s via %s' % (author_name, APPNAME))
        self.runGit(['commit', '-m', log_msg])
        if self.results['returncode'] != 0:
            logger.info("Failed to commit changes to %s" % aPath)
            logger.info("This was the error: %s" % self.results['output'])
            return -1
        else:
            self.runGit(['push'])
            if self.results['returncode'] != 0:
                logger.info("Failed to push changes to %s" % aPath)
                logger.info("This was the error: %s" % self.results['output'])
                return -1
        return 0

    def addFileAtPathForCommitter(self, aPath, aCommitter):
        """Commits a file to the Git repo."""
        self.__chdirToMatchPath(aPath)
        self.runGit(['add', aPath])
        #         We don't really need to commit each file individually, except during debugging
        #         if self.results['returncode'] == 0:
        #             self.commitFileAtPathForCommitter(aPath, aCommitter)

    def addMakeCatalogsForCommitter(self, aCommitter):
        """Commits the updated catalogs to the Git repo."""
        catalogs_path = os.path.join(REPO_DIR, 'catalogs')
        self.__chdirToMatchPath(catalogs_path)
        self.runGit(['add', catalogs_path])
        # Let's just do one commit when everything's added.
        if self.results['returncode'] == 0:
            self.commitFileAtPathForCommitter(catalogs_path, aCommitter)

    def deleteFileAtPathForCommitter(self, aPath, aCommitter):
        """Deletes a file from the filesystem and Git repo."""
        self.__chdirToMatchPath(REPO_DIR)
        self.runGit(['rm', aPath])
        # We don't really need to commit each file individually, except during debugging
        # if self.results['returncode'] == 0:
        #     self.commitFileAtPathForCommitter(aPath, aCommitter)
