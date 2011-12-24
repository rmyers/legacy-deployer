import os
import sys
import shutil
import logging
import yaml
import fcntl

from exceptions import ApiError
from exceptions import PermissionError
from exceptions import UnitDoesNotExist
from exceptions import DuplicateObject

from cannula.conf import CANNULA_BASE
from cannula.utils import Git, shell

class BaseAPI(object):
    
    model = None
    lookup_field = 'name'
    
    def get_object(self, name):
        """Get an object by the default lookup field name. Should be unique."""
        if isinstance(name, self.model):
            return name
        kwargs = {self.lookup_field: name}
        return self.model.objects.get(**kwargs)
    
    def get(self, name):
        try:
            return self.get_object(name)
        except self.model.DoesNotExist:
            raise UnitDoesNotExist
    
    def _send(self, *args, **kwargs):
        """Send a command to the remote cannula server."""

class BaseYamlAPI(object):
    
    model = None
    base_dir = ''
    
    @property
    def yaml_dir(self):
        """Return the directory that stores the yaml file objects"""
        return os.path.join(CANNULA_BASE, 'yaml', self.base_dir)
    
    def yaml_name(self, name):
        if '/' in name:
            raise ApiError("Attempted absolute path lookup?")
        return os.path.join(self.yaml_dir, '%s.yaml' % name)
    
    def initialize(self):
        if not os.path.isdir(self.yaml_dir):
            os.makedirs(self.yaml_dir)
            shell(Git.init, cwd=self.yaml_dir)
    
    def get(self, name):
        if not os.path.isdir(self.yaml_dir):
            os.makedirs(self.yaml_dir)
          
        try:
            with open(self.yaml_name(name), 'r') as f:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX|os.O_NDELAY)
                except IOError:
                    raise ApiError("Unable to lock file.")
                msg = yaml.load(f.read())
        except IOError:
            raise UnitDoesNotExist
            
        return msg
    
    def create_message(self, name, **kwargs):
        """Hook for subclasses to redefine message creation."""
        return self.model(name=name, **kwargs)
    
    def create(self, name, **kwargs):
        try:
            self.get(name)
            raise DuplicateObject()
        except UnitDoesNotExist:
            pass
        
        # Get a write lock on the file
        yml = None
        try:
            with open(self.yaml_name(name), 'w') as yml:
                try:
                    fcntl.flock(yml, fcntl.LOCK_EX|os.O_NDELAY)
                except IOError:
                    raise ApiError("Unable to lock file.")
                msg = self.create_message(name, **kwargs)
                yml.write(yaml.dump(msg))
        except:
            raise
            
        return msg
        
    def write(self, name, message):
        try:
            with open(self.yaml_name(name), 'w') as yml:
                try:
                    fcntl.flock(yml, fcntl.LOCK_EX|os.O_NDELAY)
                except IOError:
                    raise ApiError("Unable to lock file.")
                yml.write(yaml.dump(message))
        except:
            raise
        
        return True