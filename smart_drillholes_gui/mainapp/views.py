# -*- coding: utf-8 -*-

from __future__                 import unicode_literals
from .forms                     import OpenSQliteForm, OpenPostgresForm, NewForm, AddTableForm, MyModelForm, AppUserForm, GenericModelForm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy                 import String, Float, exc #(exc: Exceptions)
from django.shortcuts           import render, redirect
from django.http                import JsonResponse, Http404
from reflector.og_reflector     import Reflector
from reflector.util             import create_model, defineObject, update, pg_create, fields_generator
from reflector.bugs             import check_bugs
from smart_drillholes_gui       import settings
from django.contrib             import messages
from django.forms               import ModelForm
from django                     import forms
from smart_drillholes.core      import *
from django.urls                import reverse
import datetime
import os
import re

def generic_add(request, table_key, oid = None):
    engineURL = request.session.get('engineURL')
    reflector = Reflector(engineURL)
    reflector.reflectTables()

    exist = reflector.exist_table(table_key)
    if not exist:
        msg = "Please verify that the table: '{}' does not exist.".format(table_key)
        messages.add_message(request, messages.WARNING, msg)
        return redirect('mainapp:reflector')
    table = reflector.getOg_table(str(table_key))
    fields = fields_generator(table)
    generic_model = create_model('generic', attrs=fields)

    class MyGenericModelForm(MyModelForm):
        class Meta:
            model = generic_model
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super(MyGenericModelForm, self).__init__(*args, **kwargs)
            for field in self.fields.values():
                field.widget.attrs.update({'class': 'form-control'})

        def clean(self):
            super(MyGenericModelForm, self).clean()

            if 'FROM' and 'TO' in self.fields.keys():
                _from = self.cleaned_data.get('FROM')
                _to = self.cleaned_data.get('TO')

                if _from >= _to:
                    raise forms.ValidationError({'FROM': "FROM can't be greather or igual than TO"})

    if request.method == "POST":
        Base = declarative_base()
        generic_object = type(str(table_key), (Base,), defineObject(table))
        form = MyGenericModelForm(request.POST)
        if "update" in request.POST:
            oid = request.POST.get('oid')
            pks = eval(str(oid))
            action = ("update",pks)
        elif "insert" in request.POST:
            action = ("insert",)
        if form.is_valid():
            data = form.cleaned_data
            #Example:
            #Object_table = surveytable(BHID = 3.7, at = '2.0', az = 14.0, dip = 14.0 ,Comments = 'hello')
            #session.add(Object_table)
            session = reflector.make_session()
            if "update" in request.POST:
                Base = declarative_base()
                query = session.query(generic_object).get(pks)
                value = query.__dict__.copy()
                del value['_sa_instance_state']
                form = MyGenericModelForm(request.POST, initial = value)
                if form.has_changed():
                    cdata = form.changed_data
                    for k in form.changed_data:
                        query.__setattr__(k,data[k])
            else:
                Object_table = generic_object(**data)
                session.add(Object_table)
            try:
                session.commit()
                #session.flush()
            except exc.IntegrityError as err:
                # (psycopg2.IntegrityError) insert or update on table "assay" violates foreign key constraint "chk_bhid"
                # DETAIL:  Key (BHID)=(fddf) is not present in table "collar".
                session.rollback()
                if "violates foreign key constraint" in str(err):
                    m = re.search('(DETAIL:).+\W', str(err))
                    m = str(m.group(0)).partition("DETAIL:")
                    messages.add_message(request, messages.WARNING, m[2])
                    messages.add_message(request, messages.INFO, 'Please verify all foreign key constraints.')
                    return render(request,'mainapp/row_add.html',{'form': form, 'table_key':table_key, 'action': action})
                #postgresql UNIQUE constraint error
                elif "duplicate key value violates unique constraint" in str(err):
                    m = re.search('(DETAIL:).+\W', str(err))
                    m = str(m.group(0)).partition("DETAIL:")
                    messages.add_message(request, messages.WARNING, m[2])
                    messages.add_message(request, messages.INFO, 'Please verify all unique constraints.')
                    return render(request,'mainapp/row_add.html',{'form': form, 'table_key':table_key, 'action': action})
                #sqlite UNIQUE constraint error
                elif "UNIQUE constraint failed" in str(err):
                    m = re.search('(UNIQUE).+\[SQL', str(err))
                    m = str(m.group(0)).partition("UNIQUE")
                    m = str(m[1]) + (str(m[2]).strip('[SQL'))
                    messages.add_message(request, messages.WARNING, m)
                    messages.add_message(request, messages.INFO, 'Duplicate key value violates unique constraint.')
                    return render(request,'mainapp/row_add.html',{'form': form, 'table_key':table_key, 'action': action})
                else:
                    messages.add_message(request, messages.WARNING, str(err))
                    return render(request,'mainapp/row_add.html',{'form': form, 'table_key':table_key, 'action': action})
            except:
                raise
            finally:
                session.close()

            return redirect(reverse('mainapp:reflector', kwargs={'table_key': table_key}))
        else:
            return render(request,'mainapp/row_add.html',{'form': form, 'table_key':table_key,'action':action})

    elif oid != None and request.method == "GET":
        # form = MyGenericModelForm()
        # return render(request,'mainapp/test.html',{'data': oid})
        pks = oid.split(',')
        Base = declarative_base()
        object_table = type(str(table_key), (Base,), defineObject(table))

        if pks:
            session = reflector.make_session()
            try:
                query = session.query(object_table).get(pks)
            except exc.InvalidRequestError as err:
                messages.add_message(request, messages.WARNING, str(err))
                return redirect(reverse('mainapp:reflector', kwargs={'table_key': table_key}))
            if query:
                value = query.__dict__.copy()
                del value['_sa_instance_state']
                model = generic_model(**value)
                form = MyGenericModelForm(instance = model)
                session.close()
                action = ("update",pks)
            else:
                msg = "Please verify: The row you try to update does not exist."
                messages.add_message(request, messages.WARNING, msg)
                return redirect(reverse('mainapp:reflector', kwargs={'table_key': table_key}))

        #--------------------------------
    else:
        action = ("insert",)
        form = MyGenericModelForm()

    return render(request,'mainapp/row_add.html',{'form': form, 'table_key':table_key,'action':action})

def index(request):
    response = render(request,
                      'mainapp/index.html',
                      {'ref': 'index'})
    return response

def open(request):
    db_type = 'sqlite'
    if request.method == "GET":
        form = OpenSQliteForm()
    elif request.method == "POST":
        db_type = request.POST.get('db_type')
        if db_type == 'sqlite':
            form = OpenSQliteForm()
            if settings.files_explorer:
                selected_file = request.POST.get('selected_file')
                dbName = os.path.join(request.POST.get('current_path'),selected_file)
                if selected_file == '':
                    messages.add_message(request, messages.INFO, "Please select a sqlite database file.")

            else:
                form = OpenSQliteForm(request.POST, request.FILES)
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
            form = OpenPostgresForm(request.POST)
            if form.is_valid():
                host = form.cleaned_data.get('db_host')
                dbname = form.cleaned_data.get('db_name')
                user = form.cleaned_data.get('db_user')
                password = form.cleaned_data.get('db_password')
                con_string = 'postgresql://{2}:{3}@{0}/{1}'.format(host,dbname,user,password)

        request.session['engineURL'] = con_string
        request.session['db_type'] = db_type

        reflector = Reflector(con_string)
        error = reflector.reflectTables()

        if error:
            messages.add_message(request, messages.WARNING, error)
        else:
            cols,tks,data,table_key = update(reflector)
            return redirect('mainapp:reflector', table_key)

    return render(request,'mainapp/open.html',{'form': form, 'files_explorer': settings.files_explorer, 'directory_content': get_folder_content("/"),'db_type':db_type})

def new(request):
    if request.method == "GET":
        form = NewForm()
        return render(request,
                      'mainapp/new.html',
                      {'form': form,
                       'ref': 'new', 'files_explorer': settings.files_explorer, 'directory_content': get_folder_content("/")})
    elif request.method == "POST":
        form = NewForm(request.POST)
        if form.is_valid():
            dbname_to_create = form.cleaned_data.get('name')
            if form.cleaned_data.get('db_type') == 'sqlite':
                con_string = 'sqlite:///{}.sqlite'.format(os.path.join(request.POST.get('current_path'), dbname_to_create))
            elif form.cleaned_data.get('db_type') == 'postgresql':
                try:
                    con_string = pg_create(user = 'gramvi_admin', password = 'password', dbname_to_create = dbname_to_create)
                #database "lm" already exists
                except exc.ProgrammingError as err:
                    if "already exists" in str(err):
                        messages.add_message(request, messages.WARNING, 'Database "%s" already exists.'%(dbname_to_create))
                        messages.add_message(request, messages.INFO, 'Please verify all postgres database names.')
                        return redirect('mainapp:new')
            eng, meta = og_connect(con_string)

            try:
                og_create_dhdef(eng, meta)
            except AssertionError as err:
                if form.cleaned_data.get('db_type') == 'sqlite':
                    messages.add_message(request, messages.WARNING, 'Database "%s" already exists on path: %s.'%(dbname_to_create,request.POST.get('current_path')))
                else:
                    messages.add_message(request, messages.WARNING, str(err))
                return redirect('mainapp:new')


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

            #-Register tables on system table: OG_SMDH_SYSTEM------------------------#
            table_key = 'OG_SMDH_SYSTEM'
            tdata = [
                    {'Table':'survey','Type':'definition table','Comments':''},
                    {'Table':'collar','Type':'definition table','Comments':''},
                    {'Table':'assay_certificate','Type':'reference table','Comments':''},
                    {'Table':'rock_catalog','Type':'reference table','Comments':''},
                    {'Table':'assay','Type':'interval table','Comments':''},
                    {'Table':'litho','Type':'interval table','Comments':''}
                    ]
            reflector = Reflector(con_string)
            reflector.reflectTables()
            table = reflector.getOg_table(table_key)
            Base = declarative_base()
            generic_object = type(str(table_key), (Base,), defineObject(table))

            session = reflector.make_session()
            for data in tdata:
                Object_table = generic_object(**data)
                session.add(Object_table)
            try:
                session.commit()
                #session.flush()
            except:
                session.rollback()
            finally:
                session.close()
            #-END----------------------#
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
    #try: can raise AttributeError
    error = reflector.reflectTables()
    if error:
        messages.add_message(request, messages.WARNING, error)
        return redirect('mainapp:open')

    if table_key != '':
        exist = reflector.exist_table(table_key)
        if not exist:
            msg = "Please verify that the table: '{}' does not exist.".format(table_key)
            messages.add_message(request, messages.WARNING, msg)
            table_key = ''

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
                try:
                    session.commit()
                except exc.IntegrityError as err:
                    #DETAIL:  Key (SampleID)=(120) is still referenced from table "assay".
                    if "Key" and "is still referenced from table" in str(err):
                        m = re.search('(DETAIL:)[\w|\s|\(|\)\|=|"]+\W', str(err))
                        m = str(m.group(0)).partition("DETAIL:")
                        messages.add_message(request, messages.WARNING, m[2])
                        session.rollback()
                    else:
                        messages.add_message(request, messages.WARNING, "A unexpected error has been happened")
                        session.rollback()
                except:
                        messages.add_message(request, messages.WARNING, "A unexpected error has been happened")
                        session.rollback()
                finally:
                    session.close()

    cols,tks,data,table_key = update(reflector, table_key)

    return render(request,'mainapp/reflector.html', {'tks': tks,'cols':cols,'data':data,'table_key':table_key})

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
        form = AddTableForm()
        return render(request,
                      'mainapp/add_table.html',
                      {'ref': 'dashboard', 'form': form})
    elif request.method == 'POST':
        form = AddTableForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('table_type') == 'assay_certificate':
                og_references(eng, meta, table_name=form.cleaned_data.get('name'), key='SampleID', cols={'Au': {'coltypes': Float,
                                                                                   'nullable': True}})
            elif form.cleaned_data.get('table_type') == 'rock_catalog':
                og_references(eng, meta, table_name=form.cleaned_data.get('name'), key='RockID', cols={'Description': {'coltypes': String,
                                                                                                        'nullable': True}})
            elif form.cleaned_data.get('table_type') == 'assay':
                for column in meta.tables['assay_certificate'].columns:
                    if column.primary_key:
                        pk = column.key
                og_add_interval(eng, meta, table_name=form.cleaned_data.get('name'), cols={'SampleID': {'coltypes': String,
                                                                                  'nullable': False,
                                                                                  'foreignkey': {'column': '{}.{}'.format(table, pk),
                                                                                                 'ondelete': 'RESTRICT',
                                                                                                 'onupdate': 'CASCADE'}}})
            elif form.cleaned_data.get('table_type') == 'litho':
                table = form.cleaned_data.get('foreignkey')
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

def verify(request, table_key):
    engineURL = request.session.get('engineURL')
    reflector = Reflector(engineURL)
    reflector.reflectTables()

    exist = reflector.exist_table(table_key)
    if not exist:
        msg = "Is not posible verify bugs on: '{}', this table does not exist.".format(table_key)
        messages.add_message(request, messages.WARNING, msg)
    else:
        errors = check_bugs(reflector, table_key)
        messages.add_message(request, messages.WARNING, errors)

    return redirect(reverse('mainapp:reflector', kwargs={'table_key': table_key}))

def logout_user(request):
    logout(request)

def signup_user(request):
    if request.method == 'POST':
        signup_form = AppUserForm(request.POST)
        if signup_form.is_valid():
            new_user = AppUser.objects.create_user(
                                        username=signup_form.cleaned_data['username'],
                                        fullname=signup_form.cleaned_data['fullname'],
                                        email=signup_form.cleaned_data['email'],
                                        phone=signup_form.cleaned_data['phone'],
                                        password=signup_form.cleaned_data['password'])
            return render(request,
               'mainapp/signup.html',
               {
                'signup_form':signup_form,
               })

        else:
            return render(request,
                   'mainapp/signup.html',
                   {
                    'signup_form':signup_form,
                   })

    else:
        signup_form = AppUserForm()
        return render(request,
               'mainapp/signup.html',
               {
                'signup_form':signup_form,
               })

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
