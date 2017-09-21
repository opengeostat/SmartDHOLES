from django import forms
from django.forms import ModelForm, TextInput
from .models import AppUser

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


class OpenPostgresForm(forms.Form):
    host = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'host'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'database'}))
    user = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'required': True,
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
    name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'Set a name for the table'}))
    table_type = forms.ChoiceField(widget=forms.Select(attrs={'required': True,
                                                              'class': 'form-control'}),
                                   choices=TABLE_TYPE_CHOICES,
                                   label="Table type:")

#-------------------------------------------------------------------------------------------------------------------
# override type in phone field
class PhoneInput(TextInput):
    input_type = 'tel'

class AppUserForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(render_value=True,
                                                          attrs={'required': True,
                                                                 'class': 'form-control form-control-lg',
                                                                 'placeholder': 'Create your password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(render_value=True,
                                                                  attrs={'required': True,
                                                                         'class': 'form-control form-control-lg',
                                                                         'placeholder': 'Confirm your password'}))

    phone = forms.CharField(widget=PhoneInput(), required=False)

    class Meta:
        model = AppUser
        fields = ['username', 'fullname', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super(AppUserForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control form-control-lg',
                                                 'placeholder': 'username'})

        self.fields['fullname'].widget.attrs.update({'class': 'form-control form-control-lg',
                                                 'placeholder': 'full name'})

        self.fields['email'].widget.attrs.update({'class': 'form-control form-control-lg',
                                                  'placeholder': 'email address'})

        self.fields['phone'].widget.attrs.update({'class': 'form-control form-control-lg',
                                                  'placeholder': '+999999999',
                                                  'type': 'phone'})

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
