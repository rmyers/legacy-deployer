import os

from cannula.conf import CANNULA_BASE
from cannula.utils import write_file

class Worker(object):
    """
    Worker Class
    
    Created when a task is being run based off of the projects
    settings. These can be overwritten by the deployment.
    """
    
    template = ''
    
    def __init__(self, name, project, **kwargs):
        # The process runner, name used for templates ('uwsgi', 'gunicorn', 'fastcgi')
        self.defaults = kwargs.copy()
        if not isinstance(name, basestring):
            raise ValueError("Name must be a string!")
        if name.startswith('/'):
            raise ValueError("Name cannot start with a slash!")
        self.name = name
        self.project = project
        self.defaults['name'] = self.name
        self.defaults['project'] = self.project
    
    def script_name(self):
        return self.name
    
    def write_startup_script(self):
        """Write out startup script for worker type."""
        file_name = os.path.join(CANNULA_BASE, 'config', self.project.name, 
            self.script_name())
        
        write_file(file_name, self.template, self.defaults)
    
class gunicorn_django(Worker):
    """
    Gunicorn Django worker.
    """
        
    template = 'worker/gunicorn_django.py'
    
    def script_name(self):
        return '%s.py' % self.name