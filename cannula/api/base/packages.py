
from logging import getLogger

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import BaseAPI
from cannula.conf import api

log = getLogger('api')

class PackageAPIBase(BaseAPI):
    
    
    def _get(self, package):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def get(self, package):
        try:
            package = self._get(package)
            return package
        except:
            raise UnitDoesNotExist('Package does not exist')
    
    
    def _list(self, user=None):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def list(self, user=None):
        if user:
            user = api.users.get(user)
        return self._list(user)
    
    
    def _create(self, package, **kwargs):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def create(self, package, **kwargs):
        try:
            package = self.get(package)
            raise DuplicateObject("Package already exists!")
        except UnitDoesNotExist:
            return self._create(package, **kwargs)