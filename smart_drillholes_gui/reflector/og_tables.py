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
