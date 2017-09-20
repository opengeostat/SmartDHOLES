# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from smart_drillholes.core import *
from .forms import OpenSQliteForm, OpenPostgresForm, NewForm, AddTableForm
import datetime
from smart_drillholes_gui import settings
from django.http import JsonResponse, Http404
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Float, exc
from psycopg2 import ProgrammingError
# Views
#from django.views.decorators.csrf import csrf_exempt
#import json
from reflector.og_reflector import Reflector

import os
import re
from django.urls import reverse

from sqlalchemy import create_engine

from django.contrib import messages


def index(request):
    response = render(request,
                      'mainapp/index.html',
                      {'ref': 'index'})
    return response

def open(request):
    if request.method == "GET":
        if not settings.files_explorer:
            form = OpenSQliteForm()
        else:
            form = False
    elif request.method == "POST":
        if request.POST['db_type'] == "postgresql":
            form = OpenPostgresForm(request.POST)
        elif request.POST['db_type'] == "sqlite":
            if not settings.files_explorer:
                form = OpenSQliteForm(request.POST, request.FILES)
            db_type = request.POST.get('db_type')
            if db_type == 'sqlite':
                if settings.files_explorer:
                    dbName = os.path.join(request.POST.get('current_path'),request.POST.get('selected_file'))
                else:
                    if form.is_valid():
                        urlfile = request.FILES["sqlite_file"]
                        name = form.cleaned_data.get('sqlite_file')
                        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        dbName = BASE_DIR+'/smart4.sqlite'
                #content_type: application/octet-stream

                if dbName != '':
                    engineURL = 'sqlite:///'+dbName
                #con_string = 'sqlite:///{0}.sqlite'.format(name)
                con_string = engineURL
            elif db_type == 'postgresql':
                host = form.cleaned_data.get('host')
                dbname = form.cleaned_data.get('name')
                user = form.cleaned_data.get('user')
                password = form.cleaned_data.get('password')
                con_string = 'postgresql://{2}:{3}@{0}/{1}'.format(host,dbname,user,password)

            request.session['engineURL'] = con_string
            request.session['db_type'] = db_type

            reflector = Reflector(con_string)
            reflector.reflectTables()
            cols,tks,data,table_key = update(reflector)

            return redirect('mainapp:reflector', table_key)
            #expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=525600)
            #response.set_cookie(key='db', value=form.cleaned_data.get('name'), expires=expiry_time)
            #response.set_cookie(key='db_type', value=form.cleaned_data.get('db_type'), expires=expiry_time)
            return response
    return render(request,'mainapp/open.html',{'form': form, 'files_explorer': settings.files_explorer, 'directory_content': get_folder_content("/")})

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
            elif form.cleaned_data.get('db_type') == 'postgresql':
                dbname_to_create = form.cleaned_data.get('name')
                try:
                    con_string = pg_create(user = 'gramvi_admin', password = 'password', dbname_to_create = dbname_to_create)
                #database "lm" already exists
                except exc.ProgrammingError as err:
                    if "already exists" in str(err):
                        messages.add_message(request, messages.WARNING, 'Database "%s" already exists.'%(dbname_to_create))
                        messages.add_message(request, messages.INFO, 'Please verify all postgres database names.')
                        return redirect('mainapp:new')
            eng, meta = og_connect(con_string)

            og_create_dhdef(eng, meta)

            og_system(eng, meta)

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

#@csrf_exempt
def reflector(request, table_key = ''):
    engineURL = request.session.get('engineURL')
    reflector = Reflector(engineURL)
    reflector.reflectTables()

    if request.method == 'POST':
        pks = request.POST.getlist('checkbox-delete')
        pp = []
        for i,pk in enumerate(pks):
            pks[i] = pk.split(',')
        table_key = str(request.POST['tablename'])
        Base = declarative_base()
        table = reflector.getOg_table(str(table_key))

        object_table = type(str(table_key), (Base,), defineObject(table))

        if pks:
            session = reflector.make_session()
            for pk in pks:
                query = session.query(object_table).get(pk)
                session.delete(query)
                session.commit()
            session.close()

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

#this function update the data from database
def update(reflector, table_key = '', session = ''):
    if reflector.is_reflected():
        if session == '':
            session = reflector.make_session()

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
        cols = table.getColumnsInfo()

        #for set primary keys on checkbox delete field
        indxs = table.getPKeysIndex()
        for dt in dat:
            ids = []
            for i in indxs:
                ids.append(str(dt[i]))

            dic = {'pks':','.join(ids),'data':dt}
            data.append(dic)
    session.close()
    del reflector
    return (cols,tks,data,table_key)

def pg_create(user, password, dbname_to_create, host = "localhost", dbname_to_connect = "postgres"):
    str_engine = "postgresql://{2}:{3}@{0}/{1}".format(host,dbname_to_connect,user,password)
    engine = create_engine(str_engine)
    with engine.connect().execution_options(
            isolation_level="AUTOCOMMIT") as conn:

        #currentdb = conn.scalar("select current_database()")
        for attempt in range(3):
            try:
                #"CREATE DATABASE %s TEMPLATE %s" % (dbname_to_create, currentdb))
                conn.execute("CREATE DATABASE %s" % (dbname_to_create))
            except exc.ProgrammingError:
                raise
            except exc.OperationalError as err:
                if attempt != 2 and "accessed by other users" in str(err):
                    time.sleep(.2)
                    continue
                else:
                    raise
            else:
                conn.close()
                str_engine = "postgresql://{2}:{3}@{0}/{1}".format(host,dbname_to_create,user,password)
                break
    return str_engine

def add_table(request):
    if request.method in ['GET', 'POST']:
        #if request.COOKIES.get('db_type') == "sqlite":
        if request.session.get('db_type') == "sqlite":
            #con_string = 'sqlite:///{}.sqlite'.format(request.COOKIES.get('db'))
            con_string = request.session.get('engineURL')
        #elif request.COOKIES.get('db_type') == "postgresql":
        elif request.session.get('db_type') == "postgresql":
            #con_string = 'postgresql://postgres@localhost/{}'.format(request.COOKIES.get('db'))
            con_string = request.session.get('engineURL')
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
def get_folder_content_in_json(request):
    if settings.files_explorer:
        content = get_folder_content(request.GET.get('path'))
        return JsonResponse({'content': content})
    else:
        return Http404('You don\'t have access to this function')
def get_folder_content(path=None):
    files = []
    folders = []
    if not path:
        path = "/"
    try:
        content = os.listdir(path)
        for element in content:
            element_path = os.path.join(path, element)
            if os.path.isfile(element_path):
                files.append(element)
            elif os.path.isdir(element_path) and os.access(element_path, os.R_OK):
                folders.append(element)
    except OSError:
        return False
    return {"files":files,"folders":folders,"path":path,"previous_path":os.path.dirname(os.path.dirname(path))}
