from django import forms
from sqlalchemy import (create_engine,
                        Table,
                        Column,
                        Float,
                        String,
                        MetaData,
                        ForeignKey,
                        CheckConstraint)
DB_TYPE_CHOICES = (
    (u'sqlite', u"SQLite"),
    (u'postgresql', u"PostgreSQL")
)
TABLE_TYPE_CHOICES = (
    (u'assay_certificate', u"Assay Certificate"),
    (u'rock_catalog', u"Rock Catalog"),
    (u'assay', u"Assay"),
    (u'litho', u"Lithology"),
)


class OpenForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'Database'}))
    db_type = forms.ChoiceField(widget=forms.Select(attrs={'required': True,
                                                           'class': 'form-control'}),
                                choices=DB_TYPE_CHOICES,
                                label="Database type:"
                                )


class NewForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'Set a name for the database'}))
    db_type = forms.ChoiceField(widget=forms.Select(attrs={'required': True,
                                                           'class': 'form-control'}),
                                choices=DB_TYPE_CHOICES,
                                label="Database type:"
                                )


class AddTableForm(forms.Form):
    def __init__(self, *args, **kwargs):
        meta = kwargs.pop('meta')
        super(AddTableForm, self).__init__(*args, **kwargs)
        self.fields['foreignkey'].choices = ((x, x) for x in meta.tables.keys())

    name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'Set a name for the table'}))
    table_type = forms.ChoiceField(widget=forms.Select(attrs={'required': True,
                                                              'class': 'form-control'}),
                                   choices=TABLE_TYPE_CHOICES,
                                   label="Table type:")
    foreignkey = forms.ChoiceField(widget=forms.Select(attrs={'required': False,
                                                              'class': 'form-control'}),
                                   choices=[],
                                   label="ForeignKey:")
