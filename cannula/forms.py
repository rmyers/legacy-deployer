
from django import forms

from cannula.models import Project, ProjectGroup, Key, valid_key

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['created', 'group']

#    def __init__(self, *args, **kwargs):
#        """
#        Dynamically populate group choices.
#        """
#        self.user = kwargs.pop('user')
#        super(ProjectForm, self).__init__(*args, **kwargs)
#
#        groups = self.user.groupmembership_set.filter(add=True)
#        group_choices = [(g.group.id, g.group.name) for g in groups]
#        self.fields['group'].choices = group_choices

class ProjectGroupForm(forms.ModelForm):
    class Meta:
        model = ProjectGroup
        exclude = ['date_created', 'members']

    def __init__(self, *args, **kwargs):
        """
        Dynamically populate group choices.
        """
        self.user = kwargs.pop('user')
        super(ProjectGroupForm, self).__init__(*args, **kwargs)

class SSHKeyForm(forms.Form):
    name = forms.CharField(required=True,
        error_messages={'required': 'Please enter a name'}
    )
    ssh_key = forms.CharField(required=True,
        error_messages={'required': 'Please enter a ssh key'},
        validators=[valid_key],
    )
    