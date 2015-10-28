from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.conf import settings

from django.contrib.auth.models import User, Group
from reports.models import BusinessUnit, Machine
from guardian.shortcuts import get_objects_for_user

try:
    BUSINESS_UNITS_ENABLED = settings.BUSINESS_UNITS_ENABLED
except:
    BUSINESS_UNITS_ENABLED = False

PROJECT_DIR = settings.PROJECT_DIR


def index(request):
	#business_units = BusinessUnit.objects.all()
	business_units = get_objects_for_user(request.user, 'reports.can_view_businessunit')

	hanlde=open(PROJECT_DIR+"/../version", 'r+')
	version=hanlde.read()

	return {'business_units_enabled': BUSINESS_UNITS_ENABLED,
			'business_units': business_units,
			'webadmin_version': version}