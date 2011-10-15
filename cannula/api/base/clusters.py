
from logging import getLogger

from cannula.api import DuplicateObject, UnitDoesNotExist, BaseAPI
from cannula.conf import api

log = getLogger('api')

class ClusterAPIBase(BaseAPI):
    
    
    def _get(self, cluster):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def get(self, cluster):
        try:
            cluster = self._get(cluster)
            return cluster
        except:
            raise UnitDoesNotExist('Cluster does not exist')
    
    
    def _list(self, user=None):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def list(self, user=None):
        if user:
            user = api.users.get(user)
        return self._list(user)
    
    
    def _create(self, cluster, **kwargs):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def create(self, cluster, **kwargs):
        try:
            cluster = self.get(cluster)
            raise DuplicateObject("Cluster already exists!")
        except UnitDoesNotExist:
            return self._create(cluster, **kwargs)