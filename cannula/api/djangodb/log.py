
from django.db.models.loading import get_model

from cannula.api.base.log import LoggingAPIBase

Log = get_model('cannula', 'log')

class LoggingAPI(LoggingAPIBase):
    
    
    def _get(self, group, project, cluster=None):
        if cluster:
            logs = Log.objects.filter(group=group, project=project, cluster=cluster)
        else:
            logs = Log.objects.filter(group=group, project=project)
        logs.order_by('timestamp')
        try:
            return logs.latest()
        except Log.DoesNotExist:
            return None
    
    def _news(self, groups):
        return Log.objects.filter(group__in=groups)
        
    def _list(self, group, project, cluster=None, page=1, count=20):
        if cluster:
            logs = Log.objects.filter(group=group, project=project, cluster=cluster)
        else:
            logs = Log.objects.filter(group=group, project=project)
        logs.order_by('timestamp')
        return logs
    
    
    def _create(self, message, user, group, project, cluster):
        Log.objects.create(user=user, group=group, project=project,
                           cluster=cluster, message=message)