from datetime import datetime
import re

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os
from cannula import conf

PROJECT_RE = re.compile('^[a-zA-Z][-_a-zA-Z0-9]*$')

RESERVED_WORDS = [
    'project',
    'group',
    'admin',
    'accounts'
]

def valid_name(name):
    """Make sure project name does not have special chars or spaces."""
    if not PROJECT_RE.match(name):
        raise ValidationError("Must start with a letter and contain "
            "only letters, numbers, underscore and dashes.")
    if name in RESERVED_WORDS:
        raise ValidationError("%s is a reserved name sorry." % name)

class ProjectGroup(models.Model):
    """
    Project Group

    Collection of projects that users have access to. 
    Users can belong to multiple groups. But usually there is one 
    group per department.
    """
    name = models.SlugField(max_length=100, unique=True, db_index=True,
        validators=[valid_name])
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(User, through="GroupMembership")
    date_created = models.DateField(default=datetime.now)
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return '/%s/' % self.name
    
    class Meta:
        app_label = "cannula"
        ordering = ('name',)
    
    @property
    def members_list(self):
        return self.members.all()
    
    @property
    def projects(self):
        return self.project_set.all()
    
class GroupMembership(models.Model):
    """
    Many to Many relationship for the Project Group membership. This holds a
    little information about the user, such as the date added and the
    permission level they have.
    """
    user = models.ForeignKey(User)
    group = models.ForeignKey(ProjectGroup)
    add = models.BooleanField(default=False, blank=True)
    delete = models.BooleanField(default=False, blank=True)
    modify = models.BooleanField(default=False, blank=True)
    date_joined = models.DateField(default=datetime.now)
    
    def __unicode__(self):
        return self.group.name
    
class Project(models.Model):
    
    name = models.SlugField(max_length=255, unique=True, db_index=True,
        help_text="Project name, this should be a short and sweet "
        "unique identifier. Must contain only lowercase letters, numbers,"
        " underscores or hyphens",
        validators=[valid_name])
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(ProjectGroup,
        help_text="Group that has access.")
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return '/%s/%s/' % (self.group.name, self.name)
    
    @property
    def repo_dir(self):
        directory = '%s/%s.git' % (self.group.name, self.name)
        return os.path.join(conf.CANNULA_BASE, directory)
    
    @property
    def project_dir(self):
        directory = '%s/%s' % (self.group.name, self.name)
        return os.path.join(conf.CANNULA_BASE, directory)
    
    @property
    def unix_id(self):
        """Used for system username."""
        return u'%s.%s' % (self.group.name, self.name)
    
    @property
    def git_config(self):
        return os.path.join(self.repo_dir, 'config')
    
    @property
    def git_description(self):
        return os.path.join(self.repo_dir, 'description')
    
    @property
    def post_receive(self):
        return os.path.join(self.repo_dir, 'hooks', 'post-receive')
    
class Key(models.Model):
    
    name = models.CharField(max_length=255)
    ssh_key = models.TextField()
    
    def __unicode__(self):
        return self.name

class Profile(models.Model):
    
    user = models.ForeignKey(User)
    twitter = models.CharField(max_length=255, blank=True)
    facebook = models.CharField(max_length=255, blank=True)
    ssh_keys = models.ManyToManyField(Key)
    
    def __unicode__(self):
        return self.user

class Log(models.Model):
    """
    Logs for group/project actions.
    """
    user = models.ForeignKey(User, blank=True, null=True)
    group = models.ForeignKey(ProjectGroup, blank=True, null=True)
    project = models.ForeignKey(Project, blank=True, null=True)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=datetime.now)
    
    def __unicode__(self):
        user_str = self.user and u" by %s" % self.user or u""
        date_str = self.timestamp.strftime('on %B %d, %Y at %l:%M %p')
        return u"%s %s%s" % (self.message, date_str, user_str)
    
    class Meta:
        app_label = "cannula"
        ordering = ('-timestamp',)
        get_latest_by = ('timestamp')