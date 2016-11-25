from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.conf import settings

import os

try:
    STYLE = settings.STYLE
    APPNAME = settings.APPNAME
except:
    STYLE = 'default'
    APPNAME = "MunkiWebAdmin"

def index(request):
    return {'style': STYLE, 'APPNAME': APPNAME }
