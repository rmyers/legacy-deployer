from logging import getLogger

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models.loading import get_model

from cannula.api import UnitDoesNotExist
from cannula.api import ApiError
from cannula.api import BaseAPI

from cannula.conf import api

Log = get_model('cannula', 'log')

log = getLogger('api')

class LoggingAPIBase(BaseAPI):

    def _get(self, group, project):
        logs = Log.objects.filter(group=group, project=project)
        logs.order_by('timestamp')
        try:
            return logs.latest()
        except Log.DoesNotExist:
            return None
    
    def _news(self, groups):
        return Log.objects.filter(group__in=groups)
        
    def _list(self, group, project, page=1, count=20):
        logs = Log.objects.filter(group=group, project=project)
        logs.order_by('timestamp')
        return logs
    
    
    def _create(self, message, user, group, project, cluster):
        Log.objects.create(user=user, group=group, 
            project=project, message=message)
    
    
    def get(self, group, project):
        """Get the latest log record for this project."""
        group = api.groups.get(group)
        project = api.projects.get(project)
        try:
            return self._get(group, project)
        except:
            raise UnitDoesNotExist('Log does not exist')
    
    
    def list(self, group, project, page=1, count=20):
        """List all the logs for this project paginate the results."""
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        try:
            logs = self._list(group, project, page, count)
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
    
    def create(self, message, user=None, group=None, project=None):
        if user:
            user = api.users.get(user)
        if group:
            group = api.groups.get(group)
        if project and not group:
            raise ApiError("Must specify the group in order to log to a project")
        elif project:
            project = api.projects.get(group, project)
        return self._create(message, user, group, project)