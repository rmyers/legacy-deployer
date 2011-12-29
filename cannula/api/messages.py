
import datetime
import urllib
import hashlib
import os
from base64 import b64decode

from cannula import conf

class User(object):
    
    def __init__(self, name, email=None, first_name=None,
        last_name=None, password='!', is_admin=False, created=None):
        self.name = name
        self.email = email or '%s@localhost.com' % name
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin
        # if we don't have a created date set it now and 
        # encrypt the password if any.
        if created is None:
            self.created = datetime.datetime.now()
            self.password = self.encrypt_password(password)
        else:
            self.created = created
            self.password = password
    
    def __unicode__(self):
        name = ''
        if self.first_name:
            name += self.first_name
        if self.last_name:
            name += ' %s' % self.last_name
        if not name:
            name = self.name
        return name
    
    def check_password(self, password):
        # Check if we have a password
        if self.password is None or self.password == '!':
            return False
        
        from passlib.hash import sha512_crypt as sc
        # do we have a valid hash?
        if not sc.identify(self.password):
            return False
        
        return sc.verify(password, self.password)
    
    def encrypt_password(self, password):
        # don't set a password if none is passed
        if password == '!' or not password:
            return '!'
        
        from passlib.hash import sha512_crypt as sc
        return sc.encrypt(password)
    
    def gravatar(self, site='', size=20):
        default = '/static/cannula/img/defaulticon-%s.png' % size
        default_url = "%s%s" % (site, default)
        
        if '@localhost.com' in self.email:
            return default
        
        # return a gravatar url
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(self.email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default_url, 's':str(size)})

        return gravatar_url
    
    def has_perm(self, perm, group=None, project=None, obj=None):
        from cannula.conf import api
        return api.permissions.has_perm(self, perm, group=group, project=project, obj=obj)

class Group(object):
    
    def __init__(self, name, user=None, description='', created=None):
        self.name = name
        self.description= description
        if created is None:
            created = datetime.datetime.now()
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return '/%s/' % (self.name)
    
class Project(object):
    
    def __init__(self, name, group=None, description=''):
        self.name = name
        if isinstance(group, Group):
            self.group = group.name
        elif isinstance(group, basestring):
            self.group = group
        else:
            raise AttributeError('Group required')
        self.description = description
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return '/%s/%s/' % (self.group, self.name)
    
    #
    # Project Read-only Settings
    # 
    
    @property
    def repo_dir(self):
        """Remote repo directory, this is where projects are pushed to."""
        directory = '%s/%s.git' % (self.group, self.name)
        return os.path.join(conf.CANNULA_BASE, directory)
    
    @property
    def project_dir(self):
        """Actual working directory of the project code. Code is checked
        out here after a push.
        """
        directory = '%s/%s' % (self.group, self.name)
        return os.path.join(conf.CANNULA_BASE, directory)
    
    @property
    def conf_dir(self):
        """Project configuration directory."""
        return os.path.join(conf.CANNULA_BASE, 'config', self.name)
        
    @property
    def appconfig(self):
        """This is the file that controls all the project handlers."""
        return os.path.join(self.project_dir, 'app.yaml')
    
    @property
    def deployconfig(self):
        """Copy of the app.yaml file in the project config directory."""
        return os.path.join(self.conf_dir, 'app.yaml')
    
    @property
    def supervior_conf(self):
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


class GroupMembership(object):
    
    def __init__(self, name, add=False, modify=False, delete=False):
        # group:username
        self.name = name
        self.group, self.user = name.split(':')
        self.add = add
        self.modify = modify
        self.delete = delete

class Deployment(object):

    def __init__(self, name, **kwargs):
        self.name = name
        
class Key(object):
    
    def __init__(self, name, ssh_key='', created=None):
        self.name = name
        if created is None:
            created = datetime.datetime.now()
            # Check the key 
            self.valid_key(ssh_key)
        self.ssh_key = ssh_key
        
    
    def valid_key(self, key):
        parts = key.split()
        if not parts[0] in ['ssh-rsa', 'ssh-dsa']:
            raise ValueError("Keys must be in ssh-rsa or ssh-dsa format")
        try:
            decoded = b64decode(parts[1])
        except:
            # keys are base64 encoded
            raise ValueError("Invalid key encoding!")
        # check the encoded string header matches
        # length of header string in key stored in 4 byte
        try:
            length = ord(decoded[3])
            # string starts at the 5th byte to length
            key_type = decoded[4:length+4]
            if key_type != parts[0]:
                raise ValueError("Key type and header do not match!")
        except IndexError:
            raise ValueError("Key string too short!")