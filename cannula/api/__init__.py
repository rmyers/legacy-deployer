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

from cannula.conf import CANNULA_BASE, cache
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
    
    def _cache_name(self, name):
        return '%s:%s' % (self.base_dir, name)
    
    def _initialize(self):
        if not os.path.isdir(self.yaml_dir):
            os.makedirs(self.yaml_dir)
            shell(Git.init, cwd=self.yaml_dir)
    
    def list_all(self, fetch=False):
        """Return a list of names of all objects of this type"""
        if not os.path.isdir(self.yaml_dir):
            return []
        names = [n.replace('.yml', '') for n in os.listdir(self.yaml_dir)]
        if fetch:
            return [self.get(n) for n in names]
        return names
    
    def get(self, name):
        if not os.path.isdir(self.yaml_dir):
            os.makedirs(self.yaml_dir)
        
        if isinstance(name, self.model):
            return name
        
        msg = cache.get(self._cache_name(name))
        if msg is None:  
            try:
                with open(self.yaml_name(name), 'r') as f:
                    try:
                        fcntl.flock(f, fcntl.LOCK_EX|os.O_NDELAY)
                    except IOError:
                        raise ApiError("Unable to lock file.")
                    msg = yaml.load(f.read())
                    cache.set(self._cache_name(name), msg)
            except IOError:
                raise UnitDoesNotExist
            
        return msg
    
    def create_message(self, name, **kwargs):
        """Hook for subclasses to redefine message creation."""
        return self.model(name=name, **kwargs)
    
    def post_create(self, msg, name, **kwargs):
        pass
    
    def create(self, name, **kwargs):
        if not os.path.isdir(self.yaml_dir):
            os.makedirs(self.yaml_dir)
            
        if not kwargs.pop('force', False):
            try:
                obj = self.get(name)
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
        
        # run post create hook
        self.post_create(msg, name, **kwargs)
        cache.set(self._cache_name(name), msg)
        return msg
        
    def write(self, name, message):
        try:
            with open(self.yaml_name(name), 'w') as yml:
                try:
                    fcntl.flock(yml, fcntl.LOCK_EX|os.O_NDELAY)
                except IOError:
                    raise ApiError("Unable to lock file.")
                yml.write(yaml.dump(message))
                cache.set(self._cache_name(name), message)
        except:
            raise
        
        return True