# Django settings for munkiwebadmin project.
import os
from django.conf import global_settings
import socket

try:
    HOSTNAME = socket.gethostname()
except:
    HOSTNAME = 'localhost'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_URL = '/static/'
MEDIA_URL = "/media/"

###########################################################################
# munkiwebadmin-specific
###########################################################################
# APPNAME is user-visible web app name
APPNAME = os.getenv('APPNAME')

MUNKI_REPO_DIR = '/munkirepo'
MAKECATALOGS_PATH = '/munkitools/makecatalogs'

MEDIA_ROOT = os.path.join(MUNKI_REPO_DIR, 'icons')
ICONS_URL = MEDIA_URL

MODEL_LOOKUP_ENABLED = True
CONVERT_TO_QWERTZ = os.getenv('CONVERT_TO_QWERTZ')
VAULT_USERNAME = os.getenv('VAULT_USERNAME')

# lock info
#LOCK_MESSAGE = 'Locked by IT Support.'
#IT_NUMBER = '0000'
#PIN = '123456'

PROXY_ADDRESS = os.getenv('PROXY_ADDRESS')

DEFAULT_MANIFEST = os.getenv('DEFAULT_MANIFEST') # serial_number or hostname

STYLE = os.getenv('STYLE')

if os.path.isdir(os.path.join(MUNKI_REPO_DIR, '.git')):
    GIT_PATH = '/usr/bin/git'

#fieldkey for https://github.com/defrex/django-encrypted-fields
# mkdir fieldkeys
# keyczart create --location=fieldkeys --purpose=crypt
# keyczart addkey --location=fieldkeys --status=primary --size=256
ENCRYPTED_FIELDS_KEYDIR = '/fieldkeys'

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = 'y2k94mib_ve%c9hth=9grurdontuse1(t&his;jy-xkcd'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS')

DEBUG = False
if os.getenv('DEBUG') == 'True':
    DEBUG = True

CORS_ORIGIN_ALLOW_ALL = DEBUG
CORS_ORIGIN_WHITELIST = ()

LOGIN_EXEMPT_URLS = ()

# django ldap auth
USE_LDAP = False
KERBEROS_REALM = os.getenv('KERBEROS_REALM')

TIMEOUT = 20 # default 20

try:
    execfile("/config/settings.py")
except:
    pass

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
    'corsheaders',

    # our apps
    'api',
    'catalogs',
    'pkgsinfo',
    'manifests',
    'inventory',
    'process',
    'reports',
    'icons',
    'updates',
    'santa',
    'vault',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django_remote_auth_ldap.middleware.RemoteUserMiddleware',
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
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'munkiwebadmin.wsgi.application'

if os.getenv('DB') == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASS'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
        }
    }
if os.getenv('DB') == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASS'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
        }
    }
if os.getenv('DB') == 'mssql':
    DATABASES = {
        'default': {
            'ENGINE': 'sql_server.pyodbc',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASS'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
            'OPTIONS': {
                'driver': 'ODBC Driver 17 for SQL Server',
            },
        }
    }

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
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE')

TIME_ZONE = os.getenv('TIME_ZONE')

USE_I18N = True

USE_L10N = True

USE_TZ = True

#### end basic Django settings
if DEBUG:
    LOGLEVEL = 'DEBUG'
else:
    LOGLEVEL = 'WARNING'

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
            'filename': 'munkiwebadmin.log',
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOGLEVEL,
            'propagate': False
        },
        'munkiwebadmin': {
            'level': LOGLEVEL,
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    },
}

# needed by django-wsgiserver when using staticserve=collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
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

if USE_LDAP:
    if KERBEROS_REALM:
        AUTHENTICATION_BACKENDS = (
            'django_remote_auth_ldap.backend.RemoteUserLDAPBackend',
            'django.contrib.auth.backends.ModelBackend',
        )
    else:
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