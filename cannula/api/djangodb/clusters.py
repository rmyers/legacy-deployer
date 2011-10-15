
from django.db.models.loading import get_model

from cannula.api.base.clusters import ClusterAPIBase

Cluster = get_model('cannula', 'cluster')

class ClusterAPI(ClusterAPIBase):
    
    
    def _get(self, cluster):
        if isinstance(cluster, Cluster):
            return cluster
        cluster = Cluster.objects.get(abbr=cluster)
        return cluster
    
    
    def _list(self, user=None):
        leaf_clusters = Cluster.objects.filter(deployable=True)
        if not user or not user.is_superuser:
            leaf_clusters = leaf_clusters.filter(admin_only=False)
        return leaf_clusters
    
    
    def _create(self, cluster, **kwargs):
        node = Cluster.objects.create(abbr=cluster, **kwargs)
        return node
        