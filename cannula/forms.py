
from django import forms

from cannula.models import Project, ProjectGroup, Profile, Key
from django.contrib.auth.models import User

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['created_on']

    def __init__(self, *args, **kwargs):
        """
        Dynamically populate group choices.
        """
        self.user = kwargs.pop('user')
        super(ProjectForm, self).__init__(*args, **kwargs)

        groups = self.user.groupmembership_set.filter(can_add=True)
        group_choices = [(g.group.id, g.group.name) for g in groups]
        self.fields['group'].choices = group_choices