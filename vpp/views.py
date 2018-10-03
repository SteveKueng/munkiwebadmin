# -*- coding: utf-8 -*-
from django.http import HttpResponse, Http404
from django.shortcuts import render
from munkiwebadmin.django_basic_auth import logged_in_or_basicauth


@logged_in_or_basicauth()
def index(request):
    context = {'page': 'vpp'}
    return render(request, 'vpp/index.html', context=context)
