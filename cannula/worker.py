import os
import posixpath

from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from cannula.conf import api, proxy, CANNULA_CLUSTER_DEFAULTS, CANNULA_BASE

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
    
    def __init__(self, worker, flavor, template_base='worker'):
        # The process runner, name used for templates ('uwsgi', 'gunicorn', 'fastcgi')
        self.worker = worker
        # The type of application ('django', 'pylons', 'paste', 'php')
        self.flavor = flavor
        self.template_base = template_base
    
    def defaults(self, deployment):
        """Return a dictionary of the default values for this deployment."""
        cluster = api.clusters.get(deployment.cluster)
        defaults = CANNULA_CLUSTER_DEFAULTS.get('__all__', {})
        defaults.update(CANNULA_CLUSTER_DEFAULTS.get(cluster.abbr, {}))
        defaults.update({'deployment': deployment})
        return defaults 
    
    def deploy(self, deployment, **kwargs):
        """Deploy the deployment object. """
        defaults = self.defaults(deployment)
        # Common name for all files.
        name = '%s_%s' % (deployment.project.group.abbr,
                          deployment.project.abbr)
        # Write the wsgi file for this deployment.
        wsgi_file = os.path.join(CANNULA_BASE, self.worker, '%s.py' % name)
        wsgi_file_changed = self.write_file(wsgi_file, defaults, 
                                            template='wsgi.py')
        
        ini_file = os.path.join(CANNULA_BASE, self.worker, '%s.ini' % name)
        ini_file_changed = self.write_file(ini_file, defaults, 
                                           template='project.ini')
        # Write the proxy conf snippet.
        proxy_conf_changed = proxy.write_worker_conf(self.worker, deployment, defaults)
        
        changed = {'wsgi': wsgi_file_changed,
                   'ini': ini_file_changed,
                   'proxy': proxy_conf_changed,
        }
        return changed
        
        
    def write_file(self, filename, context, template=None):
        """
        Write file to the filesystem, if the template does not 
        exist fail silently. Otherwise write the file out and return
        boolean if the content had changed from last write. If the 
        file is new then return True.
        """
        if template is None:
            template = os.path.basename(filename)
        if '/' not in template:
            # template is not a full path, generate it now.
            template = posixpath.join(self.template_base, self.worker, template)
        try:
            content = render_to_string(template, context)
        except TemplateDoesNotExist:
            return False
        
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename), mode=0750)
        
        original_content = ''
        if os.path.isfile(filename):
            with open(filename, 'rb') as file:
                original_content = file.read()
        
        with open(filename, 'wb') as file:
            file.write(content)
        
        return content != original_content
        
    def delete(self, *args, **kwargs):
        raise NotImplementedError
    
    def modify(self, *args, **kwargs):
        """Start|stop|restart the application.
        Raises 'InvalidAction' and 'InvalidStatus'"""
        raise NotImplementedError