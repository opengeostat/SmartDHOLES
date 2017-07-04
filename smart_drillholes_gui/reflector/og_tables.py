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

    def getFKeys(self):
        return self.foreign_keys

    def getColumns(self):
        cols = []
        for column in self.columns:
            rep = str(column.name)
            cols.append(rep)

        return cols

    def setPKeys(self, primary_keys):
        self.primary_keys = primary_keys

    def setFKeys(self, foreign_keys):
        self.foreign_keys = foreign_keys

    def setColumns(self, columns):
        self.columns = columns
