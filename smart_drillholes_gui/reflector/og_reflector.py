#!/usr/bin/env python
import sys

from sqlalchemy             import MetaData, engine
from og_tables              import og_dbTable
from sqlalchemy.orm         import sessionmaker
from util                   import reflect
from error                  import EmptyError
#-reflector
class Reflector():
    def __init__(self, engineURL = ''):
        self.og_tables = {}
        self.engineURL = engineURL
        self.table_keys = []
        self.pure_tables = []
        self.reflected = False

    @reflect
    def reflectTables(self):
        try:
            self.dbengine = engine.create_engine(self.engineURL)
            self.metadata = MetaData(bind=self.dbengine, reflect=True)
        except:
            self.reflected = False
            raise
        else:
            self.table_keys = self.metadata.tables.keys()
            for tableName in sorted(self.table_keys):
                self.create_ogTable(self.metadata.tables[tableName])
            if self.table_keys == []:
                self.reflected = False
                raise EmptyError("Please verify that your database is not empty.")
            else:
                self.reflected = True

    #-showTable
    def create_ogTable(self,table):
        #temporal
        self.pure_tables.append(table)
        self.table = None
        self.table = og_dbTable(table.name)

        if len(table.primary_key):
            self.table.setPKeys(table.primary_key)

        if len(table.foreign_keys):
            self.table.setFKeys(table.foreign_keys)

        self.table.setColumns(table.c)

        self.og_tables[str(table.name.encode('utf-8',errors='replace'))] = self.table

    def exist_table(self, table_key):
        if table_key in self.table_keys:
            return True
        return False

    def getOg_tables(self):
        return self.og_tables

    def getOg_table(self, name = ''):
        return self.og_tables[name]

    def get_tableKeys(self):
        return self.table_keys

    def get_pure_tables(self):
        return self.pure_tables

    def get_metadata(self):
        return self.metadata

    def get_engine(self):
        return self.dbengine

    def make_session(self):
        DBSession = sessionmaker(bind=self.dbengine)
        return DBSession()

    def is_reflected(self):
        return self.reflected
