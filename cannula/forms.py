
from django import forms

from cannula.models import valid_name, valid_key

class ProjectForm(forms.Form):
    name = forms.CharField(required=True,
        error_messages={'required': 'Please enter a name'},
        validators=[valid_name],
        widget=forms.TextInput(attrs={
            'data-bind': 'value: name'
        })
    )
    description = forms.CharField(required=False,
        widget=forms.Textarea(attrs={
            'data-bind': 'value: description'
        })
    )
    group = forms.CharField(label='', widget=forms.HiddenInput())

class ProjectGroupForm(forms.Form):
    name = forms.CharField(required=True,
        error_messages={'required': 'Please enter a name'},
        validators=[valid_name],
        widget=forms.TextInput(attrs={
            'data-bind': 'value: name'
        })
    )
    description = forms.CharField(required=False,
        widget=forms.Textarea(attrs={
            'data-bind': 'value: description'
        })
    )

class SSHKeyForm(forms.Form):
    name = forms.CharField(required=True,
        error_messages={'required': 'Please enter a name'},
        widget=forms.TextInput(attrs={
            'data-bind': 'value: name'
        })
    )
    ssh_key = forms.CharField(required=True,
        error_messages={'required': 'Please enter a ssh key'},
        validators=[valid_key],
        widget=forms.Textarea(attrs={
            'data-bind': 'value: key'
        })
    )
    