from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.conf import settings

from reports.models import BusinessUnit, Machine

try:
    BUSINESS_UNITS_ENABLED = settings.BUSINESS_UNITS_ENABLED
except:
    BUSINESS_UNITS_ENABLED = False

def index(request):
	business_units = BusinessUnit.objects.all()
	machines_count = Machine.objects.all().count()
	return {'business_units_enabled': BUSINESS_UNITS_ENABLED,
			'business_units': business_units,
			'machines_count': machines_count}