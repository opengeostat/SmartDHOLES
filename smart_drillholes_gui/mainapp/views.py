# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from smart_drillholes.core import *
from .forms import NewForm
import datetime


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Float
# Views
#from django.views.decorators.csrf import csrf_exempt
#import json
from reflector.og_reflector import Reflector
from sqlalchemy.orm import sessionmaker
import os
import re

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

            og_create_dhdef(eng,meta)
            execute(eng,meta)
            response = redirect('mainapp:dashboard')
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=525600)
            response.set_cookie(key='db', value=form.cleaned_data.get('name'), expires=expiry_time)
            return response

def dashboard(request):
    response =  render(request,
                  'mainapp/dashboard.html',
                  {'ref': 'dashboard'})
    return response



#@csrf_exempt
def reflector(request, table_key = ''):

    if request.method == 'POST':
        pks = request.POST.getlist('checkbox-delete')
        pp = []
        for i,pk in enumerate(pks):
            pks[i] = pk.split(',')
        table_key = str(request.POST['tablename'])
        Base = declarative_base()
        table = reflector.getOg_table(str(table_key))

        object_table = type(str(table_key), (Base,), defineObject(table))

        for pk in pks:
            query = session.query(object_table).get(pk)
            session.delete(query)
            session.commit()

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dbName = BASE_DIR+'/smart4.sqlite'
    if dbName != '':
        engineURL = 'sqlite:///'+dbName
        global reflector
        reflector = Reflector(str(engineURL))
        reflector.reflectTables()

    cols,tks,data,table_key = update(reflector, table_key)

    return render(request,'mainapp/reflector.html', {'tks': tks,'cols':cols,'data':data,'table_key':table_key})

#Define database Object Table
def defineObject(table):
    columns = table.getColumns()
    tbl_def = {}
    primary_key = False
    nullable = False
    unique = False
    for column in columns:
        if column.primary_key:
            primary_key = True
        else:
            primary_key = False
        if column.nullable:
            nullable = True
        else:
            nullable = False
        if column.unique:
            unique = True
        else:
            unique = False
        tbl_def[column.name] = Column(primary_key = primary_key, nullable = nullable, unique = unique)
    tbl_def['__tablename__'] = table.getName()

    return tbl_def

def update(reflector, table_key):
    if reflector.is_reflected():
        #table list
        tableList = reflector.getOg_tables()
        DBSession = sessionmaker(bind=reflector.get_engine())
        #nonlocal session
        global session
        session = DBSession()

        #table names for template
        tks = reflector.get_tableKeys()

        data = []
        if table_key != '':
            table = reflector.getOg_table(table_key)
            dat = session.query(reflector.get_metadata().tables[table_key]).all()
        else:
            table_key = tks[0]
            table = reflector.getOg_table(table_key)
            dat = session.query(reflector.get_metadata().tables[tks[0]]).all()

        #columns for template table
        cols = table.getColumnNames()

        #for set primary keys on checkbox delete field
        indxs = table.getPKeysIndex()
        for dt in dat:
            ids = []
            for i in indxs:
                ids.append(str(dt[i]))

            dic = {'pks':','.join(ids),'data':dt}
            data.append(dic)

    return (cols,tks,data,table_key)
