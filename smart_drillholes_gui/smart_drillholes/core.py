import sqlalchemy

from sqlalchemy import (create_engine,
                        Table,
                        Column,
                        Float,
                        String,
                        MetaData,
                        ForeignKey,
                        CheckConstraint)


def og_connect(con_string='sqlite:///test2.sqlite', overwrite=False, echo=True):

    print 'connection string:', con_string
    print 'echo', echo


# get database type
    dbtype = con_string[0:5]
    if dbtype == 'sqlit':

        # TODO: check database is empty

        # Do a row connection and update some pragma
        eng = create_engine(con_string, echo=echo)
        with eng.connect() as con:
            print con.execute('PRAGMA foreign_keys = ON;')
            print con.execute('PRAGMA case_sensitive_like = True;')

    if dbtype == 'postg':
        eng = create_engine(con_string, echo=echo)

    if dbtype == 'sqlite':
        pass

    # create collar table
    meta = MetaData()
    collar = Table('collar', meta,
                   Column('BHID', String, primary_key=True),
                   Column('xcollar', Float, nullable=False),
                   Column('ycollar', Float, nullable=False),
                   Column('zcollar', Float, nullable=False),
                   Column('LENGTH', Float, nullable=False),
                   Column('Comments', String))

    survey = Table('survey', meta,
                   Column('BHID', None,
                          ForeignKey(column='collar.BHID',
                                     ondelete='CASCADE',
                                     onupdate='CASCADE',
                                     name='chk_bhid'),
                          primary_key=True),
                   Column('at', Float, nullable=False, primary_key=True),
                   Column('az', Float, nullable=False),
                   Column('dip', Float, nullable=False),
                   Column('Comments', String))

    return eng, meta


def og_add_interval(eng, meta, table_name, cols={}):

    # create interval table
    interval = Table(table_name, meta,
                     Column('BHID', None,
                            ForeignKey(column='collar.BHID',
                                       ondelete='CASCADE',
                                       onupdate='CASCADE',
                                       name='chk_bhid'),
                            primary_key=True),
                     Column('FROM', Float, nullable=False, primary_key=True),
                     Column('TO', Float, nullable=False),
                     Column('Comments', String),
                     CheckConstraint('"TO" > "FROM"', name='check_interv'))

    for col in cols:
        if 'foreignkey' in cols[col]:
            fk = ForeignKey(column=cols[col]['foreignkey']['column'],
                            ondelete=cols[col]['foreignkey']['ondelete'],
                            onupdate=cols[col]['foreignkey']['onupdate'])
            tmpcol = Column(col, None, fk)
        else:
            tmpcol = Column(col, cols[col]['coltypes'], nullable=cols[col]['nullable'])

        interval.append_column(tmpcol)


def og_references(eng, meta, table_name='assay_certificate', key='SampleID', cols={}):

    # create interval table
    interval = Table(table_name, meta,
                     Column(key, String, primary_key=True),
                     Column('Comments', String))
    for col in cols:
        tmpcol = Column(col, cols[col]['coltypes'], nullable=cols[col]['nullable'])
        interval.append_column(tmpcol)


# TODO: add some fuctions to activate/desactivate constraints 0
# TODO: implement some triggers compatible (see dialects)???

def execute(eng, meta):
    meta.create_all(eng)



