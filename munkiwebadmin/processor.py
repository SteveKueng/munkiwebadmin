from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.conf import settings

from django.contrib.auth.models import User, Group

import os
import base64

try:
    STYLE = settings.STYLE
    APPNAME = settings.APPNAME
except:
    STYLE = 'default'
    APPNAME = "MunkiWebAdmin"

def index(request):
    try:
        image = request.user.ldap_user.attrs["thumbnailPhoto"]
        imgString = base64.b64encode(image[0])
    except:
        imgString = ""
        pass

    return {'style': STYLE, 'APPNAME': APPNAME, 'userImage': imgString }