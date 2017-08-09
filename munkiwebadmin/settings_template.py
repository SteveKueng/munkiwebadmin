# Django settings for munkiwebadmin project.
import os
from django.conf import global_settings

STATIC_URL = '/static/'
MEDIA_URL = "/media/"

###########################################################################
# munkiwebadmin-specific
###########################################################################
# APPNAME is user-visible web app name
APPNAME = 'MunkiWebAdmin2'
# MUNKI_REPO_DIR holds the local filesystem path to the Munki repo
MUNKI_REPO_DIR = '/Users/Shared/munkirepo'
#MUNKI_REPO_DIR = '/Volumes/munkirepo'

MEDIA_ROOT = os.path.join(MUNKI_REPO_DIR)

ICONS_URL = "http://localhost/munki_repo/icons/"

# path to the makecatalogs binary
MAKECATALOGS_PATH = '/usr/local/munki/makecatalogs'

#imagr server url
IMAGR_URL = ''

# provide the path to the git binary if you want MunkiWebAdmin to add and commit
# manifest edits to a git repo
# if GITPATH is undefined or None MunkiWebAdmin will not attempt to do a git add
# or commit
#GIT_PATH = '/usr/bin/git'

MODEL_LOOKUP_ENABLED = True

#Define your style from styles-folder located in static
STYLE = 'default'

#fieldkey for https://github.com/defrex/django-encrypted-fields
# mkdir fieldkeys
# keyczart create --location=fieldkeys --purpose=crypt
# keyczart addkey --location=fieldkeys --status=primary --size=256
ENCRYPTED_FIELDS_KEYDIR = '/Users/Shared/mwa2test/fieldkeys'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x@hgx4r!1rm@c4lax96tx08*d1v+m$&)w1ur4-xvcqj(9as_$q'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

###########################################################################
# munkiwebadmin-specific end
###########################################################################



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third party
    
    # our apps
    'api',
    'catalogs',
    'pkgsinfo',
    'manifests',
    'process',
    'reports',
    'updates',
    'vault',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
]

ROOT_URLCONF = 'munkiwebadmin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ os.path.join(BASE_DIR, 'munkiwebadmin/templates') ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "munkiwebadmin.processor.index",
            ],
            'debug': True,
        },
    },
]

WSGI_APPLICATION = 'munkiwebadmin.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

# using sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

#### end basic Django settings

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'class':'logging.handlers.RotatingFileHandler',
            'filename': APPNAME+'.log',
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False
        },
        'munkiwebadmin': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    },
}

# needed by django-wsgiserver when using staticserve=collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, 'munkiwebadmin/collected_static')
# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'munkiwebadmin/static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# django ldap auth
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


if USE_LDAP:
    AUTHENTICATION_BACKENDS = (
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
    )
else:
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
    )

LOGIN_URL='/login/'
LOGIN_REDIRECT_URL = '/'

# who gets code error notifcations when DEBUG is False
# https://docs.djangoproject.com/en/1.9/ref/settings/#admins
ADMINS = (
     ('Local Admin', 'root@example.com'),
)
# who gets broken link notifcations when DEBUG is False
# https://docs.djangoproject.com/en/1.9/ref/settings/#managers
MANAGERS = ADMINS