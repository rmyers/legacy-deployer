import os
import posixpath

from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from cannula.conf import api, proxy, CANNULA_BASE

class DeploymentError(Exception):
    """Base class for all deployment exception classes."""

class InvalidAction(DeploymentError):
    """There was an attempt to run an invalid action"""

class InvalidStatus(DeploymentError):
    """The deployment is not in the correct state for this action."""

class Worker(object):
    """
    Worker Class
    
    Created when a task is being run based off of the projects
    settings. These can be overwritten by the deployment.
    """
    
    template = ''
    
    def __init__(self, **kwargs):
        # The process runner, name used for templates ('uwsgi', 'gunicorn', 'fastcgi')
        self.defaults = kwargs
    
    def deploy(self, **kwargs):
        """Deploy the deployment object. """
        raise NotImplementedError
    
    def refresh(self):
        """Reload/restart server."""
        raise NotImplementedError
    
class Gunicorn(Worker):
    """"""
        
        