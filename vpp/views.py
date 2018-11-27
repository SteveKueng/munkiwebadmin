# -*- coding: utf-8 -*-
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    context = {'page': 'vpp'}
    return render(request, 'vpp/index.html', context=context)
