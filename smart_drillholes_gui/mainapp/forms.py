from django import forms

DB_TYPE_CHOICES = (
    (u'sqlite', u"SQLite"),
    (u'postgresql', u"PostgreSQL")
)
class NewForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'required': True,
                                                         'class': 'form-control',
                                                         'placeholder': 'Set a name for the database'}))
    db_type = forms.ChoiceField(widget=forms.Select(attrs={'required': True,
                                                           'class': 'form-control',
                                                           'placeholder': 'Set a name for the database'}),
                                choices=DB_TYPE_CHOICES,
                                label="Database type:"
                                )
