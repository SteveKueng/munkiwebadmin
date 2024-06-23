"""
api/models.py
"""
from django.conf import settings

import os
import sys
import logging
import plistlib

LOGGER = logging.getLogger('munkiwebadmin')
MUNKI_REPO_URL = settings.MUNKI_REPO_URL
MUNKI_REPO_PLUGIN = settings.MUNKI_REPO_PLUGIN
MUNKITOOLS_DIR = settings.MUNKITOOLS_DIR

# import munkitools
sys.path.append(MUNKITOOLS_DIR)

try:
    from munkilib.admin import makecatalogslib
    from munkilib.cliutils import ConfigurationSaveError
    from munkilib.cliutils import configure as _configure
    from munkilib.cliutils import libedit
    from munkilib.cliutils import get_version, pref, path2url
    from munkilib.wrappers import (get_input,
                                readPlistFromString, writePlistToString,
                                PlistReadError, PlistWriteError)
    from munkilib import munkirepo
except ImportError:
    LOGGER.error('Failed to import munkilib')
    raise

# connect to the munki repo
try:
    repo = munkirepo.connect(MUNKI_REPO_URL, MUNKI_REPO_PLUGIN)
except munkirepo.RepoError as err:
    print(u'Repo error: %s' % err, file=sys.stderr)
    raise


class FileError(Exception):
    '''Class for file errors'''
    pass


class FileReadError(FileError):
    '''Error reading a file'''
    pass


class FileWriteError(FileError):
    '''Error writing a file'''
    pass


class FileDeleteError(FileError):
    '''Error deleting a file'''
    pass


class FileDoesNotExistError(FileError):
    '''Error when file doesn't exist at pathname'''
    pass


class FileAlreadyExistsError(FileError):
    '''Error when creating a new file at an existing pathname'''
    pass


class MunkiRepo(object):
    '''Pseudo-Django object'''
    @classmethod
    def list(cls, kind):
        '''Returns a list of available plists'''
        plists = repo.itemlist(kind)
        return plists
    
    @classmethod
    def get(cls, kind, pathname):
        '''Reads a file and returns the contents'''
        try:
            return repo.get(kind + '/' + pathname)
        except munkirepo.RepoError as err:
            LOGGER.error('Read failed for %s/%s: %s', kind, pathname, err)
            return ''

    @classmethod
    def read(cls, kind, pathname):
        '''Reads a plist file and returns the plist as a dictionary'''
        try:
            return readPlistFromString(repo.get(kind + '/' + pathname))
        except munkirepo.RepoError as err:
            LOGGER.error('Read failed for %s/%s: %s', kind, pathname, err)
            return {}
    
    @classmethod
    def write(cls, data, kind, pathname):
        '''Writes a text data to (plist) file'''
        try:
            print('Writing %s to %s/%s' % (data, kind, pathname))
            repo.put(kind + '/' + pathname, writePlistToString(data))
            LOGGER.info('Wrote %s/%s', kind, pathname)
        except munkirepo.RepoError as err:
            LOGGER.error('Write failed for %s/%s: %s', kind, pathname, err)
            raise FileWriteError(err)
        
    @classmethod
    def writedata(cls, data, kind, pathname):
        '''Writes a text data to file'''
        try:
            print('Writing %s to %s/%s' % (data, kind, pathname))
            repo.put(kind + '/' + pathname, data)
            LOGGER.info('Wrote %s/%s', kind, pathname)
        except munkirepo.RepoError as err:
            LOGGER.error('Write failed for %s/%s: %s', kind, pathname, err)
            raise FileWriteError(err)
    
    @classmethod
    def delete(cls, kind, pathname):
        '''Deletes a plist file'''
        try:
            repo.delete(kind + '/' + pathname)
            LOGGER.info('Deleted %s/%s', kind, pathname)
        except munkirepo.RepoError as err:
            LOGGER.error('Delete failed for %s/%s: %s', kind, pathname, err)
            raise FileDeleteError(err)
    
    @classmethod
    def makecatalogs(cls, output_fn=print):
        '''Calls makecatalogs'''
        try:
            makecatalogslib.makecatalogs(repo, {}, output_fn=output_fn)
        except makecatalogslib.MakeCatalogsError as err:
            LOGGER.error('makecatalogs failed: %s', err)
            raise FileError(err)

class Plist(object):
    '''Pseudo-Django object'''
    @classmethod
    def list(cls, kind):
        '''Returns a list of available plists'''
        plists = repo.itemlist(kind)
        return plists

    @classmethod
    def new(cls, kind, pathname, user, plist_data=None):
        '''Returns a new plist object'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        if os.path.exists(filepath):
            raise FileAlreadyExistsError(
                '%s/%s already exists!' % (kind, pathname))
        plist_parent_dir = os.path.dirname(filepath)
        if not os.path.exists(plist_parent_dir):
            try:
                # attempt to create missing intermediate dirs
                os.makedirs(plist_parent_dir)
            except (IOError, OSError) as err:
                LOGGER.error('Create failed for %s/%s: %s', kind, pathname, err)
                raise FileWriteError(err)
        if plist_data:
            plist = plist_data
        else:
            # create a useful empty plist
            if kind == 'manifests':
                plist = {}
                for section in [
                        'catalogs', 'included_manifests', 'managed_installs',
                        'managed_uninstalls', 'managed_updates',
                        'optional_installs']:
                    plist[section] = []
            elif kind == "pkgsinfo":
                plist = {
                    'name': 'ProductName',
                    'display_name': 'Display Name',
                    'description': 'Product description',
                    'version': '1.0',
                    'catalogs': ['development']
                }
        try:
            plistFile=open(filepath,'wb')
            plistlib.dump(plist, plistFile)
            plistFile.close()
            LOGGER.info('Created %s/%s', kind, pathname)
        except (IOError, OSError) as err:
            LOGGER.error('Create failed for %s/%s: %s', kind, pathname, err)
            raise FileWriteError(err)
        return plist

    @classmethod
    def read(cls, kind, pathname):
        '''Reads a plist file and returns the plist as a dictionary'''
        try:
            return readPlistFromString(repo.get(kind + '/' + pathname))
        except munkirepo.RepoError as err:
            LOGGER.error('Read failed for %s/%s: %s', kind, pathname, err)
            return {}

    @classmethod
    def write(cls, data, kind, pathname, user):
        '''Writes a text data to (plist) file'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        plist_parent_dir = os.path.dirname(filepath)
        if not os.path.exists(plist_parent_dir):
            try:
                # attempt to create missing intermediate dirs
                os.makedirs(plist_parent_dir)
            except OSError as err:
                LOGGER.error('Create failed for %s/%s: %s', kind, pathname, err)
                raise FileWriteError(err)
        try:
            fileref=open(filepath,'wb')
            plistlib.dump(data, fileref)
            fileref.close()
            LOGGER.info('Wrote %s/%s', kind, pathname)
        except (IOError, OSError) as err:
            LOGGER.error('Write failed for %s/%s: %s', kind, pathname, err)
            raise FileWriteError(err)

    @classmethod
    def delete(cls, kind, pathname, user):
        '''Deletes a plist file'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        if not os.path.exists(filepath):
            raise FileDoesNotExistError(
                '%s/%s does not exist' % (kind, pathname))
        try:
            os.unlink(filepath)
            LOGGER.info('Deleted %s/%s', kind, pathname)
        except (IOError, OSError) as err:
            LOGGER.error('Delete failed for %s/%s: %s', kind, pathname, err)
            raise FileDeleteError(err)


class MunkiFile(object):
    '''Pseudo-Django object'''
    @classmethod
    def get_fullpath(cls, kind, pathname):
        '''Returns full filesystem path to requested resource'''
        return os.path.join(REPO_DIR, kind, pathname)

    @classmethod
    def list(cls, kind):
        '''Returns a list of available plists'''
        files_dir = os.path.join(REPO_DIR, kind)
        files = []
        for dirpath, dirnames, filenames in os.walk(files_dir):
            # don't recurse into directories that start with a period.
            dirnames[:] = [name for name in dirnames if not name.startswith('.')]
            subdir = dirpath[len(files_dir):].lstrip(os.path.sep)
            if os.path.sep == '\\':
                files.extend([os.path.join(subdir, name).replace('\\', '/')
                              for name in filenames
                              if not name.startswith('.')])
            else:
                files.extend([os.path.join(subdir, name)
                              for name in filenames
                              if not name.startswith('.')])
        return files

    @classmethod
    def new(cls, kind, fileupload, pathname, user):
        '''Creates a new file from a file upload; returns
        FileAlreadyExistsError if the file already exists at the path'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        if os.path.exists(filepath):
            raise FileAlreadyExistsError(
                '%s/%s already exists!' % (kind, pathname))
        file_parent_dir = os.path.dirname(filepath)
        if not os.path.exists(file_parent_dir):
            try:
                # attempt to create missing intermediate dirs
                os.makedirs(file_parent_dir)
            except (IOError, OSError) as err:
                LOGGER.error(
                    'Create failed for %s/%s: %s', kind, pathname, err)
                raise FileWriteError(err)
        cls.write(kind, fileupload, pathname, user)

    @classmethod
    def write(cls, kind, fileupload, pathname, user):
        '''Retreives a file upload and saves it to pathname'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        LOGGER.debug('Writing %s to %s', fileupload, filepath)
        try:
            with open(filepath, 'wb') as fileref:
                for chunk in fileupload.chunks():
                    LOGGER.debug('Writing chunk...')
                    fileref.write(chunk)
            LOGGER.info('Wrote %s/%s', kind, pathname)
        except (IOError, OSError) as err:
            LOGGER.error('Write failed for %s/%s: %s', kind, pathname, err)
            raise FileWriteError(err)
        except Exception as err:
            LOGGER.error('Write failed for %s/%s: %s', kind, pathname, err)
            raise FileWriteError(err)

    @classmethod
    def writedata(cls, kind, filedata, pathname, user):
        '''Retreives a file upload and saves it to pathname'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        try:
            with open(filepath, 'wb') as fileref:
                fileref.write(filedata)
            LOGGER.info('Wrote %s/%s', kind, pathname)
        except (IOError, OSError) as err:
            LOGGER.error('Write failed for %s/%s: %s', kind, pathname, err)
            raise FileWriteError(err)

    @classmethod
    def delete(cls, kind, pathname, user):
        '''Deletes file at pathname'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))


        if not os.path.exists(filepath):
            raise FileDoesNotExistError(
                '%s/%s does not exist' % (kind, pathname))
        try:
            os.unlink(filepath)
            LOGGER.info('Deleted %s/%s', kind, pathname)
        except (IOError, OSError) as err:
            LOGGER.error('Delete failed for %s/%s: %s', kind, pathname, err)
            raise FileDeleteError(err)