from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.conf import settings

try:
    STYLE = settings.STYLE
except:
    STYLE = 'default'

def index(request):
    print STYLE
    return {'style': STYLE}
