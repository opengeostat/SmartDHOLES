#!/usr/bin/env python

def check_bugs(reflector, table_key):
    if reflector.is_reflected():
        session = reflector.make_session()
        data = []

        try:
            table = reflector.getOg_table(table_key)
        except KeyError:
            raise

        dat = session.query(reflector.get_metadata().tables[table_key]).all()

        #columns for template table
        cols = table.getColumnNames()
        errors = []
        table_object = reflector.get_metadata().tables[table_key]
        # if ("FROM" or "From") and ("TO" or "To") in cols:
        #     errors = session.query(table_object).filter(table_object.FROM <= table_object.TO)

        session.close()
        return errors
