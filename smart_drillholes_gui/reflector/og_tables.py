#!/usr/bin/env python
class og_dbTable:
    def __init__(self, name, primary_keys = [], foreign_keys = [], columns= []):
        self.name = name
        self.primary_keys = primary_keys
        self.foreign_keys = foreign_keys
        self.columns = columns

    def getName(self):
        return self.name

    def getPKeys(self):
        return self.primary_keys

    def getPKeysIndex(self):
        pk_indx = []
        for indx, column in enumerate(self.columns):
            if column.primary_key:
                pk_indx.append(indx)
        return pk_indx

    def getFKeys(self):
        return self.foreign_keys

    def setPKeys(self, primary_keys):
        self.primary_keys = primary_keys

    def setFKeys(self, foreign_keys):
        self.foreign_keys = foreign_keys

    def setColumns(self, columns):
        self.columns = columns

    def getColumnNames(self):
        cols = []
        for column in self.columns:
            rep = str(column.name)
            cols.append(rep)
        return cols

    def getColumns(self):
        return self.columns

    # this function return column name, if primary key, if nullable,
    # if foreign key, if unique and column type
    def getColumnsInfo(self):
        columns = []
        for column in self.columns:
            col_def = {'name':column.name,'type':column.type}
            if column.primary_key:
                col_def['primary_key'] = True
            else:
                col_def['primary_key'] = False
            if column.nullable:
                col_def['nullable'] = True
            else:
                col_def['nullable'] = False
            if column.unique:
                col_def['unique'] = True
            else:
                col_def['unique'] = False

            if self.f_keyVerify(column.name):
                col_def['foreign_key'] = True
            else:
                col_def['foreign_key'] = False
            #set a new column info into columns array
            columns.append(col_def)

        return columns

    def f_keyVerify(self, column_name):
        if self.foreign_keys:
            if column_name in [fk.column.name for fk in self.foreign_keys]: return True

        return False
