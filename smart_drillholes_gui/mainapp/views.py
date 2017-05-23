# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from smart_drillholes.core import *
from .forms import OpenForm, NewForm, AddTableForm
import datetime

# Views


def index(request):
    response = render(request,
                      'mainapp/index.html',
                      {'ref': 'index'})
    return response


def open(request):
    if request.method == "GET":
        form = OpenForm()
        return render(request,
                      'mainapp/open.html',
                      {'form': form,
                       'ref': 'open'})
    elif request.method == "POST":
        form = OpenForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('db_type') == 'sqlite':
                con_string = 'sqlite:///{}.sqlite'.format(form.cleaned_data.get('name'))
            elif form.cleaned_data('db_type') == 'postgresql':
                con_string = 'postgresql://postgres@localhost/{}'.format(form.cleaned_data.get('name'))
            eng, meta = og_connect(con_string)
            response = redirect('mainapp:dashboard')
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=525600)
            response.set_cookie(key='db', value=form.cleaned_data.get('name'), expires=expiry_time)
            response.set_cookie(key='db_type', value=form.cleaned_data.get('db_type'), expires=expiry_time)
            return response


def new(request):
    if request.method == "GET":
        form = NewForm()
        return render(request,
                      'mainapp/new.html',
                      {'form': form,
                       'ref': 'new'})
    elif request.method == "POST":
        form = NewForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('db_type') == 'sqlite':
                con_string = 'sqlite:///{}.sqlite'.format(form.cleaned_data.get('name'))
            elif form.cleaned_data('db_type') == 'postgresql':
                con_string = 'postgresql://postgres@localhost/{}'.format(form.cleaned_data.get('name'))
            eng, meta = og_connect(con_string)
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
            execute(eng, meta)
            response = redirect('mainapp:dashboard')
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=525600)
            response.set_cookie(key='db', value=form.cleaned_data.get('name'), expires=expiry_time)
            response.set_cookie(key='db_type', value=form.cleaned_data.get('db_type'), expires=expiry_time)
            return response


def dashboard(request):
    response = render(request,
                      'mainapp/dashboard.html',
                      {'ref': 'dashboard'})
    return response


def add_table(request):
    if request.method in ['GET', 'POST']:
        if request.COOKIES.get('db_type') == "sqlite":
            con_string = 'sqlite:///{}.sqlite'.format(request.COOKIES.get('db'))
        elif request.COOKIES.get('db_type') == "postgresql":
            con_string = 'postgresql://postgres@localhost/{}'.format(request.COOKIES.get('db'))
        eng, meta = og_connect(con_string)
    if request.method == 'GET':
        form = AddTableForm(meta=meta)
        return render(request,
                      'mainapp/add_table.html',
                      {'ref': 'dashboard', 'form': form})
    elif request.method == 'POST':
        form = AddTableForm(request.POST, meta=meta)
        if form.is_valid():
            if form.cleaned_data.get('table_type') == 'assay_certificate':
                og_references(eng, meta, table_name=form.cleaned_data.get('name'), key='SampleID', cols={'Au': {'coltypes': Float,
                                                                                   'nullable': True}})
            elif form.cleaned_data.get('table_type') == 'rock_catalog':
                og_references(eng, meta, table_name=form.cleaned_data.get('name'), key='RockID', cols={'Description': {'coltypes': String,
                                                                                                        'nullable': True}})
            elif form.cleaned_data.get('table_type') == 'assay':
                table = form.cleaned_data.get('foreignkey')
                for column in meta.tables[table].columns:
                    if column.primary_key:
                        pk = column.key
                og_add_interval(eng, meta, table_name=form.cleaned_data.get('name'), cols={'SampleID': {'coltypes': String,
                                                                                  'nullable': False,
                                                                                  'foreignkey': {'column': '{}.{}'.format(table, pk),
                                                                                                 'ondelete': 'RESTRICT',
                                                                                                 'onupdate': 'CASCADE'}}})
            elif form.cleaned_data.get('table_type') == 'litho':
                for column in meta.tables[table].columns:
                    if column.primary_key:
                        pk = column.key
                og_add_interval(eng, meta, table_name=form.cleaned_data.get('name'), cols={'RockID':{'coltypes': String,
                                                                               'nullable': True,
                                                                               'foreignkey': {'column': '{}.{}'.format(table, pk),
                                                                                              'ondelete': 'RESTRICT',
                                                                                              'onupdate': 'CASCADE'}}})
            execute(eng, meta)
        return redirect('mainapp:dashboard')
