# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from smart_drillholes.core import *
from .forms import NewForm
import datetime

# Views


def index(request):
    response =  render(request,
                  'mainapp/index.html',
                  {'ref': 'index'})
    return response

def new(request):
    if request.method == "GET":
        form = NewForm()
        return render(request,
                      'mainapp/new.html', {'form': form,
                                           'ref': 'new'})
    elif request.method == "POST":
        form = NewForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('db_type') == 'sqlite':
                con_string = 'sqlite:///%s.sqlite' % form.cleaned_data.get('name')
            elif form.cleaned_data('db_type') == 'postgresql':
                con_string = 'postgresql://postgres@localhost/%s' % form.cleaned_data.get('name')
            eng, meta = og_connect(con_string, overwrite=False)
            og_references(eng, meta, table_name='assay_certificate', key='SampleID', cols={'Au': {'coltypes': Float,
                                                                                           'nullable': True}})
            og_references(eng, meta, table_name='rock_catalog', key='RockID', cols={'Description': {'coltypes': String,
                                                                                                    'nullable': True}})
            og_add_interval(eng, meta, table_name='assay', cols={'SampleID': {'coltypes': String,
                                                                              'nullable': False,
                                                                              'foreignkey': {'column': 'assay_certificate.SampleID',
                                                                                             'ondelete': 'RESTRICT',
                                                                                             'onupdate': 'CASCADE'}}})
            og_add_interval(eng, meta, table_name='litho', cols={'RockID':{'coltypes': String,
                                                                           'nullable': True,
                                                                           'foreignkey': {'column': 'rock_catalog.RockID',
                                                                                          'ondelete': 'RESTRICT',
                                                                                          'onupdate': 'CASCADE'}}})
            response = redirect('mainapp:dashboard')
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=525600)
            response.set_cookie(key='db', value=form.cleaned_data.get('name'), expires=expiry_time)
            return response

def dashboard(request):
    response =  render(request,
                  'mainapp/dashboard.html',
                  {'ref': 'dashboard'})
    return response
