from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.auth.models import User, Group

import os
import base64

# get settings
try:
    STYLE = settings.STYLE
except:
    STYLE = 'default'

try:
    APPNAME = settings.APPNAME
except:
    APPNAME = "MunkiWebAdmin"

try:
    BASE_DIR = settings.BASE_DIR
except:
    BASE_DIR = ""

try:
    HOSTNAME = settings.HOSTNAME
except:
    HOSTNAME = "localhost"

REPOSADO = False
if os.listdir('/reposado') != []:
    REPOSADO = True

def index(request):
    try:
        image = request.user.ldap_user.attrs["thumbnailPhoto"]
        imgString = "data:image/png;base64,"+base64.b64encode(image[0])
    except:
        imgString = static('img/placeholder.jpg')
        pass

    return {'style': STYLE, 'APPNAME': APPNAME, 'REPOSADO': REPOSADO, 'HOSTNAME': HOSTNAME, 'userImage': imgString }

