from datetime import datetime
import re
from base64 import b64decode

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

def valid_key(key):
    parts = key.split()
    if not parts[0] in ['ssh-rsa', 'ssh-dsa']:
        raise ValidationError("Keys must be in ssh-rsa or ssh-dsa format")
    try:
        decoded = b64decode(parts[1])
    except:
        # keys are base64 encoded
        raise ValidationError("Invalid key encoding!")
    # check the encoded string header matches
    # length of header string in key stored in 4 byte
    try:
        length = ord(decoded[3])
        # string starts at the 5th byte to length
        key_type = decoded[4:length+4]
        if key_type != parts[0]:
            raise ValidationError("Key type and header do not match!")
    except IndexError:
        raise ValidationError("Key string too short!")
    

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
    
    def to_dict(self):
        d = {
             'name': self.name,
             'description': self.description,
             'projects': [p.to_dict() for p in self.projects],
        }
        return d
    
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
    
    def to_dict(self):
        return {
            'name': self.name, 
            'description': self.description, 
            'group': self.group.name,
            'url': self.get_absolute_url()
        }
    
    #
    # Project Read-only Settings
    # 
    
    @property
    def repo_dir(self):
        """Remote repo directory, this is where projects are pushed to."""
        directory = '%s/%s.git' % (self.group.name, self.name)
        return os.path.join(conf.CANNULA_BASE, 'repos', directory)
    
    @property
    def project_dir(self):
        """Actual working directory of the project code. Code is checked
        out here after a push.
        """
        directory = '%s/%s' % (self.group.name, self.name)
        return os.path.join(conf.CANNULA_BASE, 'repos', directory)
    
    @property
    def conf_dir(self):
        """Project configuration directory."""
        return os.path.join(conf.CANNULA_BASE, 'config', self.name)
    
    @property
    def virtualenv(self):
        """Project specific environment."""
        return os.path.join(self.conf_dir, 'venv')
        
    @property
    def appconfig(self):
        """This is the file that controls all the project handlers."""
        return os.path.join(self.project_dir, 'app.yaml')
    
    @property
    def deployconfig(self):
        """Copy of the app.yaml file in the project config directory."""
        return os.path.join(self.conf_dir, 'app.yaml')
    
    @property
    def supervisor_conf(self):
        """Configuration file for controling processes."""
        return os.path.join(self.conf_dir, 'supervisor.conf')
    
    @property
    def bin_dir(self):
        """Holds startup files for processes."""
        return os.path.join(self.conf_dir, 'bin')
    
    @property
    def vhost_conf(self):
        """Configuration file for proxy vhosts."""
        return os.path.join(self.conf_dir, 'vhost.conf')
    
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
    
    user = models.ForeignKey(User)
    name = models.CharField(max_length=255)
    ssh_key = models.TextField(validators=[valid_key])
    
    def __unicode__(self):
        return self.name
    
    def to_dict(self):
        return {'name': self.name, 'ssh_key': self.ssh_key}
    
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

class Deployment(models.Model):
    """Deployment instance of a project."""
    project = models.ForeignKey(Project)
    user = models.ForeignKey(User)
    oldrev = models.CharField(max_length=100)
    newrev = models.CharField(max_length=100)
    conf_oldrev = models.CharField(max_length=100)
    conf_newrev = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=datetime.now)
    
    class Meta:
        app_label = "cannula"
    
    def __unicode__(self):
        return "Deployment of: %s @ %s" % (self.project, self.newrev)