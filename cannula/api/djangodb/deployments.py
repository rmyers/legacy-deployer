
from django.db.models.loading import get_model

from cannula.api.base.deployments import DeploymentAPIBase

Deployment = get_model('cannula', 'deployment')

class DeploymentAPI(DeploymentAPIBase):
    
    
    def _get(self, group, project, cluster):
        deployment = Deployment.objects.get(
            project=project, cluster=cluster, active=True)
        return deployment
    
    
    def _list(self, group, project, cluster, active_only, inactive_only):
        qs = project.deployment_set.all().order_by('cluster__order')

        if active_only:
            qs = qs.filter(active=True)
        elif inactive_only:
            qs = qs.filter(active=False)
        
        if cluster:
            qs = qs.filter(cluster=cluster)
        return qs
    
    
    def _create(self, group, project, cluster, url, package,
               repo_path, revision=None, current=None):
        values = {
            'project': project,
            'cluster': cluster,
            'url': project.url,
            'package': package,
            'revision': revision,
            'repo_path': repo_path,
        }
        return Deployment.objects.create(**values)