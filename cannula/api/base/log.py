from logging import getLogger

from django.core.paginator import Paginator, EmptyPage, InvalidPage

from cannula.api import UnitDoesNotExist
from cannula.api import ApiError
from cannula.api import BaseAPI

from cannula.conf import api

log = getLogger('api')

class LoggingAPIBase(BaseAPI):
    
    
    def _get(self, group, project, cluster=None):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    
    def get(self, group, project, cluster=None):
        """Get the latest log record for this project."""
        group = api.groups.get(group)
        project = api.projects.get(project)
        if cluster:
            cluster = api.clusters.get(cluster)
        try:
            return self._get(group, project, cluster)
        except:
            raise UnitDoesNotExist('Log does not exist')
    
    
    def _list(self, group, project, cluster=None, page=1, count=20):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    
    def list(self, group, project, cluster=None, page=1, count=20):
        """List all the logs for this project paginate the results."""
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        if cluster:
            cluster = api.clusters.get(cluster)
        try:
            logs = self._list(group, project, cluster, page, count)
        except:
            logs = []
        
        # Paginate the logs
        paginator = Paginator(logs, count)
        try:
            page = int(page)
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            p_logs = paginator.page(page)
        except (EmptyPage, InvalidPage):
            p_logs = paginator.page(paginator.num_pages)

        return p_logs
    
    def _news(self, groups):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    def news(self, groups, page=1, count=20):
        """List all actions for a list of groups."""
        logs = self._news(groups)
        paginator = Paginator(logs, count)
        try:
            page = int(page)
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            p_logs = paginator.page(page)
        except (EmptyPage, InvalidPage):
            p_logs = paginator.page(paginator.num_pages)

        return p_logs
    
    def _create(self, message, user, group, project, cluster):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    
    def create(self, message, user=None, group=None, project=None, cluster=None):
        if user:
            user = api.users.get(user)
        if group:
            group = api.groups.get(group)
        if project and not group:
            raise ApiError("Must specify the group in order to log to a project")
        elif project:
            project = api.projects.get(group, project)
        if cluster:
            cluster = api.clusters.get(cluster)
        return self._create(message, user, group, project, cluster)