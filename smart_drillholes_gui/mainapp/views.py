# -*- coding: utf-8 -*-

from __future__                                   import unicode_literals
from .forms                                       import (OpenSQliteForm, OpenPostgresForm,
                                                         NewForm, AddTableForm,MyModelForm,
                                                         AppUserForm, GenericModelForm,
                                                         FormTableColumn)
from sqlalchemy.schema                            import ForeignKeyConstraint, DropConstraint
from sqlalchemy.ext.declarative                   import declarative_base
from sqlalchemy                                   import String, Float, Integer, exc #(exc: Exceptions)
from smart_drillholes.reflector.og_reflector      import Reflector
from smart_drillholes.reflector.util              import (create_model, defineObject,
                                                          update, pg_create, fields_generator,
                                                          connection_str, tb_data,
                                                          adapt_postgresToSqlite, removeOnCascade,
                                                          depend)
from smart_drillholes.reflector.bugs              import check_bugs
from smart_drillholes_gui                         import settings
from smart_drillholes.core                        import *
from django.contrib.auth.decorators               import login_required
from django.shortcuts                             import render, redirect
from django.http                                  import JsonResponse, Http404
from django.contrib                               import messages
from django.forms                                 import ModelForm, formset_factory
from django                                       import forms
from django.urls                                  import reverse
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

@login_required
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
                dbName = form.cleaned_data.get('db_name')
                user = form.cleaned_data.get('db_user')
                password = form.cleaned_data.get('db_password')
                con_string = 'postgresql://{2}:{3}@{0}/{1}'.format(host,dbName,user,password)

        request.session['engineURL'] = con_string
        request.session['db_type'] = db_type
        request.session['db_name'] = dbName

        reflector = Reflector(con_string)
        error = reflector.reflectTables()

        if error:
            messages.add_message(request, messages.WARNING, error)
        else:
            cols,tks,data,table_key = update(reflector)
            return redirect('mainapp:dashboard')

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
            db_type = form.cleaned_data.get('db_type')
            dbname_to_create = form.cleaned_data.get('name')
            if db_type == 'sqlite':
                con_string = 'sqlite:///{}.sqlite'.format(os.path.join(request.POST.get('current_path'), dbname_to_create))
            elif db_type == 'postgresql':
                try:
                    con_string = pg_create(user = 'gramvi_admin', password = 'password', dbname_to_create = dbname_to_create)
                #database "lm" already exists
                except exc.ProgrammingError as err:
                    if "already exists" in str(err):
                        messages.add_message(request, messages.WARNING, 'Database "%s" already exists.'%(dbname_to_create))
                        messages.add_message(request, messages.INFO, 'Please verify all postgres database names.')
                        return redirect('mainapp:new')

            error = False
            try:
                eng, meta = og_connect(con_string)
                #Create drillhole definition tables in the metadata, collar and survey.
                og_create_dhdef(eng, meta)
            except AssertionError as err:
                if db_type == 'sqlite':
                    messages.add_message(request, messages.WARNING, 'Database "%s" already exists on path: %s.'%(dbname_to_create,request.POST.get('current_path')))
                else:
                    messages.add_message(request, messages.WARNING, str(err))
                error = True
            except exc.OperationalError as err:
                if "unable to open database file" in str(err):
                    messages.add_message(request, messages.WARNING, 'Unable to create sqlite database file "%s.sqlite" on path: %s.'%(dbname_to_create,request.POST.get('current_path')))
                else:
                    messages.add_message(request, messages.WARNING, str(err))
                error = True
            except:
                raise

            if error: return redirect('mainapp:new')

            og_system(eng, meta)

            og_references(eng, meta, table_name='assay_certificate', key='SampleID', cols={'Au': {'coltypes': Float,
                                                                                           'nullable': True}})
            og_references(eng, meta, table_name='rock_catalog', key='RockID', cols={'Description': {'coltypes': String,
                                                                                                    'nullable': True}})
            og_add_interval(eng, meta, table_name='assay', cols={'SampleID': {'coltypes': String,
                                                                              'nullable': False,
                                                                              'foreignkey': {'column': 'assay_certificate.SampleID',
                                                                                             'ondelete': 'CASCADE',
                                                                                             'onupdate': 'CASCADE'}}})
            og_add_interval(eng, meta, table_name='litho', cols={'RockID':{'coltypes': String,
                                                                           'nullable': True,
                                                                           'foreignkey': {'column': 'rock_catalog.RockID',
                                                                                          'ondelete': 'CASCADE',
                                                                                          'onupdate': 'CASCADE'}}})

            execute(eng, meta)

            #-Register tables on system table: OG_SMDH_SYSTEM------------------------#
            table_key = 'OG_SMDH_SYSTEM'
            tdata = [
                    {'Table':'survey','Type':'definition (survey)','Comments':''},
                    {'Table':'collar','Type':'definition (collar)','Comments':''},
                    {'Table':'assay_certificate','Type':'reference','Comments':''},
                    {'Table':'rock_catalog','Type':'reference','Comments':''},
                    {'Table':'assay','Type':'interval','Comments':''},
                    {'Table':'litho','Type':'interval','Comments':''}
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
            request.session['engineURL'] = con_string
            request.session['db_type'] = db_type
            request.session['db_name'] = dbname_to_create
            return redirect('mainapp:dashboard')

def dashboard(request):
    eng = request.session.get('engineURL')
    db_tp = request.session.get('db_type')
    db_nm = request.session.get('db_name')
    if not connection_str(request):
        return redirect('mainapp:index')
    return render(request,'mainapp/dashboard.html', {'ref': 'dashboard'})

def close_connection(request):
    connection_str(request, clean = True)
    return redirect('mainapp:index')

#@csrf_exempt
def reflector(request, table_key = ''):
    engineURL = request.session.get('engineURL')
    if not engineURL:
        messages.add_message(request, messages.WARNING, message = "Please open a database.")
        return redirect('mainapp:open')
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
        pks = request.POST.getlist('checkbox_delete')
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
        RowFormset = formset_factory(FormTableColumn, extra=1, max_num=15)
        db_type = request.session.get('db_type')
        if db_type == "sqlite" or db_type == "postgresql":
            #con_string = 'sqlite:///{}.sqlite'.format(request.COOKIES.get('db'))
            #con_string = 'postgresql://postgres@localhost/{}'.format(request.COOKIES.get('db'))
            con_string = request.session.get('engineURL')
        eng, meta = og_connect(con_string)
    if request.method == 'GET':
        form = AddTableForm()

        return render(request,
                      'mainapp/add_table.html',
                      {'ref': 'dashboard', 'form': form, 'formset':RowFormset})
    elif request.method == 'POST':
        form = AddTableForm(request.POST)
        formset = RowFormset(request.POST)

        if form.is_valid() and formset.is_valid():
            table_name = form.cleaned_data.get('table_name')
            reflector = get_reflector(request)
            exist = reflector.exist_table(table_name)

            if exist:
                msg = "The table '{}', already exist.".format(table_name)
                messages.add_message(request, messages.INFO, msg)
                return render(request,'mainapp/add_table.html',{'form': form, 'formset':formset})

            formset_cols = {}

            # formset
            for fform in formset:
                name = fform.cleaned_data.get('name')
                tb_type = fform.cleaned_data.get('tb_type')
                if tb_type == 'String':
                    tb_type = String
                elif tb_type == 'Float':
                    tb_type = Float
                elif tb_type == "Integer":
                    tb_type = Integer
                nullable = fform.cleaned_data.get('nullable')
                formset_cols[name] = {'coltypes':tb_type, 'nullable': nullable}
            table_type = form.cleaned_data.get('table_type')
            #insert assay_certificate, rock_catalog, other_reference table types
            if table_type == 'assay_certificate' or table_type == 'rock_catalog' or table_type == 'other_reference':
                #defaults on template client side:
                #cols = {'Au': {'coltypes': Float,'nullable': True}}
                # on assay_certificate key=SampleID
                # on rock_catalog key=RockID
                # on other_reference key=''
                table_key = request.POST.get('ftable_key')
                cols = formset_cols
                og_references(eng, meta, table_name=table_name, key=str(table_key), cols=cols)

            elif table_type == 'assay' or table_type == 'litho':
                # on this tables, collar foreignkey: collar.BHID
                table_reference = request.POST.get('table_reference')
                raise Error
                for column in meta.tables[table_reference].columns:
                    if column.primary_key:
                        pk = column.key
                cols = {pk:{'coltypes': String,
                                'nullable': False,
                                'foreignkey': {'column': '{}.{}'.format(table_reference, pk),
                                            'ondelete': 'CASCADE',
                                            'onupdate': 'CASCADE'}}}
                cols.update(formset_cols)
                og_add_interval(eng, meta, table_name=table_name, cols=cols)
            #other_interval
            elif table_type == 'other_interval':
                # on this tables, collar foreignkey: dbsuffix+_collar.BHID
                collar_reference = request.POST.get('collar_reference')
                raise Error
                if collar_reference and collar_reference.endswith('_collar'):
                    m = re.search("_collar", collar_reference)
                    dbsuffix = collar_reference[:m.start()]
                elif collar_reference == 'collar':
                    dbsuffix = ''

                table_reference = request.POST.get('table_reference')
                for column in meta.tables[table_reference].columns:
                    if column.primary_key:
                        pk = column.key
                cols = {pk: {'coltypes': String,
                            'nullable': False,
                            'foreignkey': {'column': '{}.{}'.format(table_reference, pk),
                                            'ondelete': 'CASCADE',
                                            'onupdate': 'CASCADE'}}}
                cols.update(formset_cols)
                og_add_interval(eng, meta, table_name=table_name, cols=cols, dbsuffix = dbsuffix)
            try:
                execute(eng, meta)
            except exc.NoReferencedTableError:
                msg = "Please verify: there are tables really does not exists or are wrong."
                messages.add_message(request, messages.WARNING, msg)
                return redirect(reverse('mainapp:reflector'))
            except:
                raise
            #-Register table on system table: OG_SMDH_SYSTEM------------------------#
            og_register_table = 'OG_SMDH_SYSTEM'

            if table_type == 'other_interval' or table_type == 'assay' or table_type == 'litho':
                tbtype = 'interval'
            elif table_type == 'assay_certificate' or table_type == 'rock_catalog' or table_type == 'other_reference':
                tbtype = 'reference'
            tdata = {'Table':table_name,'Type':tbtype,'Comments':''}
            reflector = Reflector(con_string)
            reflector.reflectTables()
            table = reflector.getOg_table(og_register_table)
            Base = declarative_base()
            generic_object = type(str(og_register_table), (Base,), defineObject(table))

            session = reflector.make_session()
            Object_table = generic_object(**tdata)
            session.add(Object_table)
            try:
                session.commit()
                #session.flush()
            except:
                session.rollback()
            finally:
                session.close()
            #end register
        else:
            return render(request,'mainapp/add_table.html',{'form': form, 'formset':formset})
        return redirect('mainapp:reflector')

from sqlalchemy.schema                            import DropTable, DropConstraint
from sqlalchemy.ext.compiler                      import compiles

@compiles(DropTable, "postgresql")
def _compile_drop_table(element, compiler, **kwargs):
    return compiler.visit_drop_table(element) + " CASCADE"


def remove_table(request):
    engineURL = request.session.get('engineURL')
    reflector = Reflector(engineURL)
    reflector.reflectTables()
    meta = reflector.get_metadata()

    if request.method == 'POST':
        tbl = request.POST.get('tbl')
        db_type = request.session.get('db_type')
        removeOnCascade(db_type, reflector,tbl)

        reflector.reflectTables()
        meta = reflector.get_metadata()

    return redirect('mainapp:reflector')

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

def get_collar_reference_tables_in_json(request):
    engineURL = request.session.get('engineURL')
    reflector = Reflector(engineURL)
    reflector.reflectTables()
    data = tb_data(reflector, table_key = 'OG_SMDH_SYSTEM')
    content = {'collars':[],'references':[]}
    for row in data:
        if row[1] == 'definition (collar)':
            content['collars'].append(row[0])
        if row[1] == 'reference':
            content['references'].append(row[0])
    return JsonResponse({'content': content})

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

#this function return reflector object of request engine
def get_reflector(request):
    engineURL = request.session.get('engineURL')
    reflector = Reflector(engineURL)
    reflector.reflectTables()
    return reflector

# ---------------------------------------------------------
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
# Adapt postgres DOUBLE_PRECISION type to sqlite FLOAT type
@compiles(DOUBLE_PRECISION, 'sqlite')
def compile_DOUBLE_PRECISION_postgresql_sqlite(element, compiler, **kw):
    """ Handles postgresql DOUBLE_PRECISION datatype as FLOAT in sqlite """
    res = compiler.visit_FLOAT(element, **kw)
    return res

def postgres_to_sqlite(request):
    engineURL = request.session.get('engineURL')
    db_name = request.session.get('db_name')
    db_type = request.session.get('db_type')
    str_sqlite_meta = 'sqlite:////home/leudis/Desktop/{}.sqlite'.format(db_name)
    adapted = False
    if db_type == 'postgresql':
        adapted = adapt_postgresToSqlite(engineURL,str_sqlite_meta)
    if adapted:
        msg = "The '{}' postgres database was succefull adapted to sqlite, enjoy this.".format(db_name)
        messages.add_message(request, messages.SUCCESS, msg)
    else:
        msg = "The '{}' database was not succefull adapted.".format(db_name)
        messages.add_message(request, messages.WARNING, msg)

    return redirect(reverse('mainapp:dashboard'))

def test_json(request):
    engineURL = request.session.get('engineURL')
    table_key = request.GET.get("tk")
    reflector = Reflector(engineURL)
    db_type = request.session.get('db_type')
    content = depend(db_type,reflector,table_key)
    # content = depend(db_type,reflector,"collar")
    # content = {'hola':{"lolo":{"lola":"null"}}}
    return JsonResponse({'content': content})
    # return render(request,'mainapp/test.html',{'data': content})
