import os
from django.conf import global_settings

##############################
# MunkiWeb-specific settings #
##############################

# APPNAME is user-visable web app name
APPNAME = 'MunkiWebAdmin'
# MUNKI_REPO_DIR holds the local filesystem path to the Munki repo
MUNKI_REPO_DIR = '/Users/Shared/munkirepo'
ICONS_DIR = 'icons'
# provide the path to the git binary if you want MunkiWeb to add and commit
# manifest edits to a git repo
# if GITPATH is undefined or None MunkiWeb will not attempt to do a git add
# or commit
GIT_PATH = ''

# name of the key in a manifest file that names the user or dept
MANIFEST_USERNAME_KEY = 'user'
# set MANIFEST_USERNAME_IS_EDITABLE to allow edits to the displayed username
MANIFEST_USERNAME_IS_EDITABLE = False

# enable WARRANTY to show warranty information on the detail machine report
WARRANTY_LOOKUP_ENABLED = True

# managed updates visible in manifests
MANAGED_UPDATES_ENABLED = False

# display SSH-Button in detal view
SSH_BUTTON_ENABLED = False

# display VNC-Button in detal view
VNC_BUTTON_ENABLED = False

#if true all software packages are shown in autocompletion not only the one in included catalogs
ALL_ITEMS = False

#user serial_number or hostname for client manifest
CLIENT_MANIFEST = 'serial_number'

# enable MODEL_LOOKUP_ENABLED to show a human readable version of the machines model
MODEL_LOOKUP_ENABLED = True

# enable Business units
BUSINESS_UNITS_ENABLED = False

# if MunkiWebAdmin is behind a proxy, and WARRANTY_LOOKUP_ENABLED or
# MODEL_LOOKUP_ENABLED are enabled, enter the details for the proxy server in
# the format user:password@example.com:port (user:password@ and :port are
# optional), otherwise leave blank
PROXY_ADDRESS = ""

# needed for productive mode
ALLOWED_HOSTS = ['*']

# imagr config / needed for staging tab in reports
IMAGR_CONFIG_URL = ""

TOKEN_TIMEOUT_DAYS = 1

ANONYMOUS_USER_ID = -1
# -------------------------

USE_LDAP = False
# LDAP authentication support
if USE_LDAP:
    import ldap
    from django_auth_ldap.config import LDAPSearch, PosixGroupType

    # LDAP settings
    AUTH_LDAP_SERVER_URI = "ldap://foo.example.com"
    AUTH_LDAP_BIND_DN = ""
    AUTH_LDAP_BIND_PASSWORD = ""
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        "ou=People,o=ExampleCorp,c=US",
        ldap.SCOPE_SUBTREE, "(uid=%(user)s)")
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
        "ou=Groups,o=ExampleCorp,c=US",
        ldap.SCOPE_SUBTREE, "(objectClass=posixGroup)")
    AUTH_LDAP_GROUP_TYPE = PosixGroupType()
    AUTH_LDAP_FIND_GROUP_PERMS = True
    AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName",
                               "last_name": "sn",
                               "email": "mail"}
    # Cache group memberships for an hour to minimize LDAP traffic
    AUTH_LDAP_CACHE_GROUPS = True
    AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('Admin', 'admin@mydomain.com'),
)

MANAGERS = ADMINS

# using sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(PROJECT_DIR, 'munkiwebadmin.db'),                      # Or path to database file if using sqlite3.
        'USER': '',     # Not used with sqlite3.
        'PASSWORD': '', # Not used with sqlite3.
        'HOST': '', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '', # Set to empty string for default. Not used with sqlite3.
    }
}

# mysql example
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': 'munkiweb',
#        'USER': 'munkiwebuser',
#        'PASSWORD': 'munkiwebuserpasswd',
#        'HOST': 'munkiwebdb.example.org',
#        'PORT': '',
#    }
#}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Zurich'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'de-CH'

# -----------------

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

MEDIA_ROOT = os.path.join(MUNKI_REPO_DIR, ICONS_DIR)

MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'site_static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'x@hgx4r!1rm@c4lax96tx88*d1v+m$&)w1ur4-xvcqj(8as_$q'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    "munkiwebadmin.processor.index",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

if USE_LDAP:
    AUTHENTICATION_BACKENDS = (
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
        'tokenapi.backends.TokenBackend',
    )
else:
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'tokenapi.backends.TokenBackend',
    )

LOGIN_URL='/login/'
LOGIN_REDIRECT_URL='/computer/dashboard'

ROOT_URLCONF = 'munkiwebadmin.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'guardian',
    'tokenapi',
    'reports',
    'catalogs',
    'manifests',
    'inventory',
    'licenses',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
     },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
	    'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
