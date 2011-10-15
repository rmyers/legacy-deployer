
from django.db.models.loading import get_model

from cannula.api.base.unix_id import UnixIDAPIBase

UnixID = get_model('cannula', 'unixid')

class UnixIDAPI(UnixIDAPIBase):
    
    
    def _get(self, group, project, cluster):
        return UnixID.objects.get(project=project, cluster=cluster)
    
    
    def _list(self, group, project, cluster=None):
        query = {'project': project}
        if cluster:
            cluster = self.get_cluster(cluster)
            query['cluster'] = cluster
        # Should either return the existing ID or generate new one.
        return UnixID.objects.filter(**query)
    
    
    def _create(self, group, project, cluster):
        return UnixID.objects.generate_id(project, cluster)
