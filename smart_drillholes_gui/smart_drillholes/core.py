import sqlalchemy


from sqlalchemy import (create_engine,
                        Table,
                        Column,
                        Float,
                        String,
                        MetaData,
                        ForeignKey,
                        CheckConstraint)


def og_connect(con_string='sqlite:///test2.sqlite', echo=False):
    """og_connect(con_string='sqlite:///test2.sqlite', echo=False)

    Create a connection to a database and returns connection and metadata

    Parameters
    ----------
    con_string : str (default 'sqlite:///test2.sqlite')
                 connection string to a database, e.g.
                'sqlite:///test2.sqlite'
                 'postgresql://postgres@localhost/Dhole'

                see http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls for more info

    echo :      bool (default False)
                print database server log output


    Returns
    -------
    eng : sqlalchemy engine
        active connection to a database
    meta : sqlalchemy metadata
        container object that keeps together many different features of a database


    Example
    -------
    >>> con_string= 'postgresql://postgres@localhost/Dhole'
    >>> eng, meta = og_connect(con_string, echo=False)

    """

    # print 'connection string:', con_string
    # print 'echo', echo

    # get database type
    dbtype = con_string[0:5]
    if dbtype == 'sqlit':

        # Do a row connection and update some pragma
        eng = create_engine(con_string, echo=echo)
        with eng.connect() as con:
            print con.execute('PRAGMA foreign_keys = ON;')
            print con.execute('PRAGMA case_sensitive_like = True;')

    if dbtype == 'postg':
        eng = create_engine(con_string, echo=echo)

    # if dbtype == 'sqlite':
    #     pass

    # create collar table
    meta = MetaData()
    meta.reflect(bind=eng)

    return eng, meta


def og_create_dhdef(eng, meta, dbsuffix="", collar_cols={}, survey_cols={}):
    """og_create_dhdef(eng, meta, dbsuffix="", collar_cols={}, survey_cols={})

    Create drillhole definition tables in the metadata, collar and survey.
    If you have more than one of drillhole use ``dbsuffix``,
    e.g. ``dbsuffix= Historic`` will create tables
    Historic_collar and Historic_survey

    Default culumns BHID, xcollar, ycollar, zcollar, LENGTH, and Comments
    will be automatically created. To add extra columns use ``collar_cols`` and
    ``survey_cols``. Thise are dictionaries with column definition. Two options
    are available:

    a) To add a new column without external reference

        {Column1_name:{'coltypes':sqlalchemy.Data_Type, 'nullable': True/False},
         Column2_name:{'coltypes':sqlalchemy.Data_Type, 'nullable': True/False},
         ...
         ColumnN_name:{'coltypes':sqlalchemy.Data_Type, 'nullable': True/False}}

    b) To add a new column with external reference

        {Column1_name:{'coltypes':String,
                       'nullable': True,
                       'foreignkey':{'column':reference_table.reference_column,
                                     'ondelete':'RESTRICT',
                                     'onupdate':'CASCADE'}},
        ...}



    Parameters
    ----------
    eng : sqlalchemy engine
            active connection to a database

    meta : sqlalchemy metadata
            container object that keeps together many different features of a database

    dbsuffix : str (default "")
            this suffix will be added to each table_name

    collar_cols : dict (default {})
            definition of new non default columns in table collar

    survey_cols : dict (default {})
            definition of new non default columns in table survey

    Example
    -------
    >>> og_create_dhdef(eng, meta, dbsuffix="Historic",
                      collar_cols={'Company':{'coltypes':String, 'nullable': True}},
                      survey_cols={'Method' :{'coltypes':String, 'nullable': True}})

    """

    assert 'collar' not in eng.table_names(), 'Collar table: {} already in database'.format('collar')
    assert 'survey' not in eng.table_names(), 'Surbey table: {} already in database'.format('survey')

    collar = Table('collar', meta,
                   Column('BHID', String, primary_key=True),
                   Column('xcollar', Float, nullable=False),
                   Column('ycollar', Float, nullable=False),
                   Column('zcollar', Float, nullable=False),
                   Column('LENGTH', Float, nullable=False),
                   Column('Comments', String))

    survey = Table('survey', meta,
                   Column('BHID', None,
                          ForeignKey(column=dbsuffix+'_collar.BHID',
                                     ondelete='CASCADE',
                                     onupdate='CASCADE',
                                     name='chk_bhid'),
                          primary_key=True),
                   Column('at', Float, nullable=False, primary_key=True),
                   Column('az', Float, nullable=False),
                   Column('dip', Float, nullable=False),
                   Column('Comments', String))

    for ccol in collar_cols:
        if 'foreignkey' in collar_cols[ccol]:
            fk = ForeignKey(column=collar_cols[ccol]['foreignkey']['column'],
                            ondelete=collar_cols[ccol]['foreignkey']['ondelete'],
                            onupdate=collar_cols[ccol]['foreignkey']['onupdate'])
            tmpcol = Column(ccol, None, fk)
        else:
            tmpcol = Column(ccol, collar_cols[ccol]['coltypes'], nullable=collar_cols[ccol]['nullable'])

        collar.append_column(tmpcol)

    for scol in survey_cols:
        if 'foreignkey' in survey_cols[scol]:
            fk = ForeignKey(column=survey_cols[scol]['foreignkey']['column'],
                            ondelete=survey_cols[scol]['foreignkey']['ondelete'],
                            onupdate=survey_cols[scol]['foreignkey']['onupdate'])
            tmpcol = Column(scol, None, fk)
        else:
            tmpcol = Column(scol, survey_cols[scol]['coltypes'], nullable=survey_cols[scol]['nullable'])

        survey.append_column(tmpcol)


def og_add_interval(eng, meta, table_name, cols={}, dbsuffix=""):
    """og_add_interval(eng, meta, table_name, cols={}, dbsuffix="")

    Create drillhole interval tables in the metadata, eg. assay or log.
    You may need the same ``dbsuffix`` used to create the table definitions.

    Default culumns BHID, FROM, TO, and Comments
    will be automatically created. To add extra columns use ``cols``,
    a dictionary with column definition. Two options are available:

    a) To add a new column without external reference

        {Column1_name:{'coltypes':sqlalchemy.Data_Type, 'nullable': True/False},
         Column2_name:{'coltypes':sqlalchemy.Data_Type, 'nullable': True/False},
         ...
         ColumnN_name:{'coltypes':sqlalchemy.Data_Type, 'nullable': True/False}}

    b) To add a new column with external reference

        {Column1_name:{'coltypes':String,
                       'nullable': True,
                       'foreignkey':{'column':reference_table.reference_column,
                                     'ondelete':'RESTRICT',
                                     'onupdate':'CASCADE'}},
        ...}


    Parameters
    ----------
    eng : sqlalchemy engine
            active connection to a database

    meta : sqlalchemy metadata
            container object that keeps together many different features of a database

    table_name : str
            table name

    cols : dict (default {})
            definition of new non default columns

    Example
    -------
    >>> og_add_interval(eng, meta,
                        table_name = 'assay',
                        dbsuffix="Historic",
                        cols={'SampleID':{'coltypes':String,
                                          'nullable': False,
                                          'foreignkey':{'column':'assay_certificate.SampleID',
                                                        'ondelete':'RESTRICT',
                                                        'onupdate':'CASCADE'}},
                             'Au_visual':{'coltypes':Float, 'nullable': True}})

    """
    # create interval table
    interval = Table(table_name, meta,
                     Column('BHID', None,
                            ForeignKey(column=dbsuffix+'_collar.BHID',
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


def og_references(eng, meta, table_name, key='SampleID', cols={}):
    """og_references(eng, meta, table_name, key='SampleID', cols={})

    Create reference tables in the metadata, eg. assay certificates or Lithology catalog.

    Reference tables will not use external references and columns may be formatted as:

        {Column1_name:{'coltypes':sqlalchemy.Data_Type, 'nullable': True/False},
         ...}


    Parameters
    ----------
    eng : sqlalchemy engine
            active connection to a database

    meta : sqlalchemy metadata
            container object that keeps together many different features of a database

    table_name : str
            table name

    key : str (Default 'SampleID')
            name of the reference columns, it will be used as table key and
            will not allow duplicates

    cols : dict (default {})
            definition of new non-default columns

    Example
    -------
    >>> og_references(eng, meta, table_name = 'assay_certificate',
                      key = 'SampleID', cols={'Au':{'coltypes':Float, 'nullable': True}})
    >>> og_references(eng, meta, table_name = 'rock_catalog',
                      key = 'RockID', cols={'Description':{'coltypes':String, 'nullable': True}})


    """

    # create interval table
    interval = Table(table_name, meta,
                     Column(key, String, primary_key=True),
                     Column('Comments', String))
    for col in cols:
        tmpcol = Column(col, cols[col]['coltypes'], nullable=cols[col]['nullable'])
        interval.append_column(tmpcol)


def og_system(eng, meta):
    """og_system(eng, meta)

    Create a table for internal use in the metadata ```meta``` in the database connected to ``eng``.
    Parameters
    ----------
    eng : sqlalchemy engine
            active connection to a database

    meta : sqlalchemy metadata
            container object that keeps together many different features of a database

    """
    collar = Table('OG_SMDH_SYSTEM', meta,
                   Column('Table', String, primary_key=True),
                   Column('Type', String, nullable=False),
                   Column('Comments', String))


# TODO: add some functions to activate/disactivate constraints
# TODO: implement some triggers compatible (see dialects)???

def execute(eng, meta):
    """execute(eng, meta)

    Create all tables stored in the metadata ```meta``` in the database connected to ``eng``.

    Parameters
    ----------
    eng : sqlalchemy engine
            active connection to a database

    meta : sqlalchemy metadata
            container object that keeps together many different features of a database

    """
    meta.create_all(eng)
