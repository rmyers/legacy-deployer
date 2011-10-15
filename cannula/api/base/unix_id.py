
from logging import getLogger

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import BaseAPI
from cannula.conf import api

log = getLogger('api')

class UnixIDAPIBase(BaseAPI):
    
    
    def _get(self, group, project, cluster):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def get(self, group, project, cluster):
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        cluster = api.clusters.get(cluster)
        # Should either return the existing ID or generate new one.
        return self._get(group, project, cluster)
    
    
    def _list(self, group, project, cluster=None):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def list(self, group, project, cluster=None):
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        if cluster is not None:
            cluster = api.clusters.get(cluster)
        return self._list(group, project, cluster)
    
    
    def _create(self, group, project, cluster):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def create(self, group, project, cluster):
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        cluster = api.clusters.get(cluster)
        try:
            self.get(group, project, cluster)
            raise DuplicateObject("Unix ID already exists!")
        except UnitDoesNotExist:
            return self._create(group, project, cluster)