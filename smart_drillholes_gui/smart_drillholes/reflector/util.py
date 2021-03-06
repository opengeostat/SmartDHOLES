#!/usr/bin/env python

import re
from django.db                  import models
from sqlalchemy                 import MetaData, Column, create_engine, exc
from sqlalchemy.engine          import reflection
from error                      import EmptyError
from django.core.validators     import RegexValidator

#-1-create_model
#-2-defineObject
#-3-update
#-4-pg_create
#-5-fields_generator
#-6-reflect
#-7-connection_str
#-8-tb_data
#-9-adapt_postgresToSqlite
#-10-removeOnCascade

#-1------------------Dinamic Model------------------------#
def create_model(name, attrs={}, meta_attrs={}, module_path='django.db.models'):
    attrs['__module__'] = module_path
    class Meta:
        pass

    setattr(Meta, 'app_label', 'reflector')

    Meta.__dict__.update(meta_attrs, __module__ = module_path)
    attrs['Meta'] = Meta
    return type(str(name), (models.Model,), attrs)

#-2-----------------------------------------#
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

#-3----------------------------------------------------------#
#this function update the data from database
def update(reflector, table_key = '', session = None):
    if reflector.is_reflected():
        if session == None:
            session = reflector.make_session()
        #table names for template
        tks = reflector.get_tableKeys()
        data = []
        if table_key != '':
            try:
                table = reflector.getOg_table(table_key)
            except KeyError:
                raise
            dat = session.query(reflector.get_metadata().tables[table_key]).all()
        else:
            try:
                table_key = tks[0]
            except IndexError:
                raise
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

#-4--------------------------------------------------------#
# this function create new database on postgres
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
#-5----------------------------------------------------#
# this function generate fields for the generic model
def fields_generator(table):
    fields = {}
    #fields = {
        #'first_name': models.CharField(max_length=255),
        #'last_name': models.CharField(max_length=255),
        #'__unicode__': lambda self: '%s %s' (self.first_name, self.last_name),
    #}
    columns = table.getColumns()
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

        if column.type:
            col_type = column.type.__visit_name__

        if column.type:
            try:
                col_len = column.type.length
                if col_len == None:
                    col_len = 255
            except:
                col_len = 255

        if col_type in ['FLOAT', 'DOUBLE_PRECISION']:
            fields[column.name] = models.FloatField(primary_key = primary_key, blank=nullable, null=nullable, unique=unique)
        elif col_type in ['VARCHAR']:
            if primary_key:
                validator = [RegexValidator('^[\w-]+$', 'Enter a valid string. This value may contain only letters, numbers and - or _ characters.', 'invalid')]
            else: validator = []
            fields[column.name] = models.CharField(max_length = col_len, primary_key = primary_key, blank=nullable, null=nullable, unique=unique, validators= validator)
        elif col_type in ['TEXT']:
            fields[column.name] = models.TextField(primary_key = primary_key, blank=nullable, null=nullable, unique=unique)
        elif col_type in ['INTEGER']:
            fields[column.name] = models.IntegerField(primary_key = primary_key, blank=nullable, null=nullable, unique=unique)
        elif col_type in ['SMALLINT']:
            fields[column.name] = models.SmallIntegerField(primary_key = primary_key, blank=nullable, null=nullable, unique=unique)
        elif col_type in ['BOOLEAN']:
            if nullable:
                fields[column.name] = models.NullBooleanField(primary_key = primary_key, blank=nullable, null=nullable, unique=unique)
            else:
                fields[column.name] = models.BooleanField(primary_key = primary_key, blank=nullable, null=nullable, unique=unique)
        else:
            fields[column.name] = models.CharField(primary_key = primary_key, blank=nullable, null=nullable, unique=unique, validators=[RegexValidator('^[\w\s-]+$', 'Enter a valid string. This value may contain only letters, numbers and -/_ characters.', 'invalid')])

        #fields['__unicode__'] = lambda self: '%s' (self.name),

    return fields

#-6------------------DECORATOR-1-----------------------#
# this is a decorator function that reflect tables on database or raise a error message
def reflect(reflect_tables):
    def wrapper(self):
        message = None
        try:
            return reflect_tables(self)
        except exc.OperationalError as err:
            #FATAL:  password authentication failed for user "gramvi_admin"
            if "password authentication failed for user" in str(err):
                m = re.search('(FATAL:){1}[\w|\s|\(|\)\|=|"]+"', str(err))
                m = str(m.group(0)).partition("FATAL:")
                message = m[2]
                return message.strip()+'.'
                #FATAL:  database "q" does not exist
            elif "database" and "does not exist" in str(err):
                m = re.search('(FATAL:)[\w|\s|\(|\)\|=|"]+\W', str(err))
                m = str(m.group(0)).partition("FATAL:")
                message = str(m[2])
                return message.strip()+'.'
            elif "unable to open database file" in str(err):
                message = "Unable to open database file."
                return message
                # could not connect to server
            elif "could not connect to server" or "could not translate host name" in str(err):
                message = "Could not connect to server. Please verify your host."
                return message
            else:
                raise
        except exc.DatabaseError as err:
            if "file is encrypted or is not a database" in str(err):
                message = "File is encrypted or is not a database."
                return message
            else:
                raise
        except EmptyError as err:
            message = err.value
            return message
        except AttributeError as err:
            if "'NoneType' object has no attribute '_instantiate_plugins'" in str(err):
                message = "Please open a database."
                return message
            else:
                raise

        except:
            raise
    return wrapper

#-7-----------------------CLEAN------------------------#
# this function clean string connection
def connection_str(request, clean = False):
    if clean:
        request.session['engineURL'] = None
        request.session['db_type'] = None
        request.session['db_name'] = None
        return False

    eng = request.session.get('engineURL')
    db_tp = request.session.get('db_type')
    db_nm = request.session.get('db_name')
    if eng == None or db_tp == None or db_nm == None:
        return False
    return True

#-8----------------------------------------------------------#
#this function return the data from database table
def tb_data(reflector, table_key = '', session = None):
    if reflector.is_reflected():
        if session == None:
            session = reflector.make_session()

        if table_key != '':
            try:
                table = reflector.getOg_table(table_key)
            except KeyError:
                raise
            dat = session.query(reflector.get_metadata().tables[table_key]).all()
        else:
            return []


        session.close()
        del reflector
    return dat

#-9----------------------------------------------------------#
#this function adapt postgres database to sqlite database
def adapt_postgresToSqlite(str_postgres_meta, str_sqlite_meta):
    #'postgres://postgres:password@localhost/test'
    str_postgres = str_postgres_meta
    str_sqlite = str_sqlite_meta

    try:
        dbengine = create_engine(str_postgres)
        meta_postgres = MetaData(bind=dbengine, reflect=True)

        #meta_postgres = MetaData(str_postgres_meta,reflect=True)
        meta_sqlite = MetaData(str_sqlite_meta)
        for table in meta_postgres.sorted_tables:
            table.tometadata(meta_sqlite)
        meta_sqlite.create_all()
        return True
    except:
        return False


#-10----------------------------------------------------------#
#this function drop database table on cascade
def removeOnCascade(db_type, reflector, tbl):
    reflector.reflectTables()
    meta = reflector.get_metadata()
    engine = reflector.get_engine()
    #sqlite
    table_drop = tbl
    if db_type == "sqlite":
        remove_table(meta, engine, table_drop)
    #postgres
    elif db_type == "postgresql":
        sql= str("select r.relname"
        +" FROM pg_stat_user_tables r, pg_constraint c, pg_stat_user_tables s"
        +" WHERE s.relid = c.confrelid AND c.conrelid = r.relid AND"
        +" s.relname = '%s'")%table_drop
        execute = engine.execute
        try:
            result = [name for (name, ) in execute(sql)]
        except:
            raise
        tableList = []
        for tb_name in result:
            tableList.append(meta.tables[tb_name])
        table = meta.tables[table_drop]
        table.drop(checkfirst=True)
        meta.drop_all(tables=tableList, checkfirst=True)

def remove_table(meta, engine, table_drop):
    inspector = reflection.Inspector.from_engine(engine)
    table_names = inspector.get_table_names()
    table_names.remove(table_drop)

    tables_drop = []
    for table_name in table_names:
        fks = inspector.get_foreign_keys(table_name)
        referred_tables = [fk['referred_table'] for fk in fks]
        if table_drop in referred_tables:
            tables_drop.append(table_name)
    if tables_drop == []:
        table = meta.tables[table_drop]
        table.drop(checkfirst=True)
    else:
        for tb in tables_drop:
            remove_table(meta, engine, tb)
        table = meta.tables[table_drop]
        table.drop(checkfirst=True)

#-11----------------------------------------------------------#
def depend(db_type, reflector, tbl, dep = None):
    if dep == None : dep = {}
    reflector.reflectTables()
    meta = reflector.get_metadata()
    engine = reflector.get_engine()
    table_dep = tbl

    #sqlite
    if db_type == "sqlite":
        dep = dep_sqlite(engine, table_dep)
        if dep == "null":
            dep = {table_dep:"null"}
    #postgres
    elif db_type == "postgresql":
        sql= str("select r.relname"
        +" FROM pg_stat_user_tables r, pg_constraint c, pg_stat_user_tables s"
        +" WHERE s.relid = c.confrelid AND c.conrelid = r.relid AND"
        +" s.relname = '%s'")%table_dep
        execute = engine.execute
        try:
            tables = {name:"null" for (name, ) in execute(sql)}
            # return tables
        except:
            raise
        if tables != {}:

            dep[table_dep] = tables
            #return dep
            for tb in tables.keys():
                depend(db_type,reflector,tb, tables)
            return dep
        else:
            dep[table_dep] = "null"
    return dep

def dep_sqlite(engine, table_dep, dep = None):
    if dep == None : dep = {}
    inspector = reflection.Inspector.from_engine(engine)
    table_names = inspector.get_table_names()
    table_names.remove(table_dep)
    tables_dep = []
    for table_name in table_names:
        fks = inspector.get_foreign_keys(table_name)
        referred_tables = [fk['referred_table'] for fk in fks]
        if table_dep in referred_tables:
            tables_dep.append(table_name)
    if tables_dep == []:
        return "null"
    else:
        dep[table_dep] = {tb:dep_sqlite(engine, tb) for tb in tables_dep}
        return dep
