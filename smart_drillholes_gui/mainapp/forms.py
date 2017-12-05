from django import forms
from django.forms import ModelForm, TextInput
from .models import AppUser

DB_TYPE_CHOICES = (
    (u'sqlite', u"SQLite"),
    (u'postgresql', u"PostgreSQL")
)

TYPE_CHOICES = (
    (u'String', u"STRING"),
    (u'Float', u"FLOAT"),
    (u'Integer', u"INTEGER")
)

TABLE_TYPE_CHOICES = (
    ('References',(
    (u'assay_certificate', u"Assay Certificate"),
    (u'rock_catalog', u"Rock Catalog"),
    (u'other_reference', u"Other Reference Table"),
    )),

    ('Interval',(
    (u'assay', u"Assay"),
    (u'litho', u"Lithology"),
    (u'other_interval', u"Other Interval Table"),
    )),
)

class OpenPostgresForm(forms.Form):
    db_host = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'host'}))
    db_name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'database'}))
    db_user = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'DB user'}))
    db_password = forms.CharField(widget=forms.PasswordInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'password'}))
    db_type = forms.ChoiceField(widget=forms.Select(attrs={'required': True,
                                                           'class': 'form-control'}),
                                choices=DB_TYPE_CHOICES,
                                label="Database type:"
                                )

class OpenSQliteForm(forms.Form):

    sqlite_file = forms.CharField(widget=forms.FileInput(attrs={'required': True}))
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
    table_name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'Set a name for the table',
                                                         'pattern': '[a-zA-Z0-9]+\w*[a-zA-Z0-9]+'
                                                         }))
    table_type = forms.ChoiceField(widget=forms.Select(attrs={'required': True,
                                                              'class': 'form-control custom-select'}),
                                   choices=TABLE_TYPE_CHOICES,
                                   label="Table type:")

class AppUserForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(render_value=True,
                                                          attrs={'required': True,
                                                                 'class': 'form-control form-control-lg',
                                                                 'placeholder': 'Create your password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(render_value=True,
                                                                  attrs={'required': True,
                                                                         'class': 'form-control form-control-lg',
                                                                         'placeholder': 'Confirm your password'}))

    class Meta:
        model = AppUser
        fields = ['username', 'fullname']

    def __init__(self, *args, **kwargs):
        super(AppUserForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control form-control-lg',
                                                 'placeholder': 'username'})

        self.fields['fullname'].widget.attrs.update({'class': 'form-control form-control-lg',
                                                 'placeholder': 'full name'})

    def clean(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password and password != confirm_password:
            raise forms.ValidationError({'confirm_password': "Passwords don't match"})

        return self.cleaned_data

#------------Generic Model Form-----------------#
class GenericModelForm(ModelForm):
    class Meta:
        fields = '__all__'

from django.utils import six
from django.forms.models import ModelFormMetaclass, BaseModelForm

class MyBaseModelForm(BaseModelForm):
    def clean(self):
        self._validate_unique = False
        return self.cleaned_data

class MyModelForm(six.with_metaclass(ModelFormMetaclass, MyBaseModelForm)):
    pass

class FormTableColumn(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control inp_name',
                                                         'placeholder': 'name',
                                                         'onchange': 'myinput(this);',
                                                         'pattern':'[a-zA-Z0-9]+\w*[a-zA-Z0-9]+'}),
                                                         label="Column Name:"
                                                         )

    tb_type = forms.ChoiceField(widget=forms.Select(attrs={'required': True,
                                                           'class': 'form-control'}),
                                choices=TYPE_CHOICES,
                                label="Column Type:"
                                )

    nullable = forms.BooleanField(required=False ,widget=forms.CheckboxInput(attrs={'class':'custom-control-input d-none'}), label="Null:")
