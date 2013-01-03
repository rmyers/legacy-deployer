
from django import forms

from cannula.models import valid_name, valid_key
from django.core.exceptions import ValidationError

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

class ImportField(forms.CharField):
    """Special field that makes sure it is importable."""
    
    def validate(self, value):
        super(ImportField, self).validate(value)
        from cannula.utils import import_object
        try:
            import_object(value)
        except (ImportError, AttributeError):
            raise ValidationError("Could not import %s are you sure it is on your path?" % value)
    

class SettingsForm(forms.Form):
    """
    Configure cannula settings itself.
    """
    
    true_false = (
        ('true', 'True'),
        ('false', 'False')
    )
    # Basic cannula settings
    cannula_base = forms.CharField(
        help_text="Base Directory that cannula manages, must be writable by cannula user.")
    cannula_cmd= forms.CharField(
        help_text="Path to cannulactl command.")
    cannula_ssh_cmd=forms.CharField(
        help_text="Path to canner.sh, used in authorized_keys to handle authorization.")
    cannula_git_cmd=forms.CharField(
        help_text="Path to git if not on PATH.")
    cannula_template_dir=forms.CharField(required=False,
        help_text="Path to template files to override defaults.")
    # Proxy
    proxy_cmd = forms.CharField()
    proxy_needs_sudo = forms.ChoiceField(choices=true_false)
    # Proc
    proc_manages_proxy = forms.ChoiceField(choices=true_false)
    proc_use_inet = forms.ChoiceField(choices=true_false,
        help_text="You probably want this False unless you know what your doing.")
    proc_inet_port = forms.CharField()
    proc_user = forms.CharField(required=False,
        help_text="Only used with inet.")
    proc_password = forms.CharField(required=False,
        help_text="Only required with inet.")
    # api
    api_deploy = ImportField()
    api_groups = ImportField()
    api_keys = ImportField()
    api_log = ImportField()
    api_permissions = ImportField()
    api_proc = ImportField()
    api_projects = ImportField()
    api_proxy = ImportField()
    api_users = ImportField()
    # database
    database_engine = ImportField()
    database_name = forms.CharField()
    database_user = forms.CharField(required=False)
    database_password = forms.CharField(required=False)
    database_host = forms.CharField(required=False)
    database_port = forms.CharField(required=False)
    
    # Django specific
    django_debug = forms.ChoiceField(choices=true_false)
    django_site_id = forms.IntegerField()
    django_use_i18n = forms.ChoiceField(choices=true_false)
    django_use_l10n = forms.ChoiceField(choices=true_false)
    django_time_zone = forms.CharField()
    django_language_code = forms.CharField()
    django_media_url = forms.CharField()
    django_admin_media_prefix = forms.CharField()
    django_secret_key = forms.CharField()
    