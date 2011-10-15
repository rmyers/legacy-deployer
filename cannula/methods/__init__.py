try:
    import json
except ImportError:
    from django.utils import simplejson as json

from cannula.conf import api

class DeploymentError(Exception):
    """Base class for all deployment exception classes."""

class InvalidAction(DeploymentError):
    """There was an attempt to run an invalid action"""

class InvalidStatus(DeploymentError):
    """The deployment is not in the correct state for this action."""

class DeploymentMethod(object):
    """Base Deployment Method class."""
    
    @classmethod
    def defaults(cls, cluster):
        """Return a dictionary of the default values for this cluster."""
        cluster = api.clusters.get(cluster)
        return json.loads(cluster.defaults)
        
    
    @classmethod
    def create_project(cls, *args, **kwargs):
        raise NotImplementedError
    
    @classmethod
    def deploy_project(cls, *args, **kwargs):
        raise NotImplementedError
    
    @classmethod
    def delete_deployment(cls, *args, **kwargs):
        raise NotImplementedError
    
    @classmethod
    def modify_deployment(cls, *args, **kwargs):
        """Raises 'InvalidAction' and 'InvalidStatus'"""
        raise NotImplementedError