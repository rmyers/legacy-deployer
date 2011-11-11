import os
import sys
import yaml

from logging import getLogger

from django.db.models.loading import get_model

from cannula.api import BaseAPI, ApiError
from cannula.conf import api, proxy, CANNULA_GIT_CMD
from cannula.utils import write_file, shell, import_object

log = getLogger('api')

class Handler(object):
    """Simple object to hold properties for wsgi handlers"""
    
    def __init__(self, name, worker, **kwargs):
        self._worker_klass = import_object(worker)
        self._worker_obj = self._worker_klass(name, **kwargs)
    
    def __getattr__(self, attr):
        return getattr(self._worker_obj, attr)
    
class DeployAPI(BaseAPI):
    
    def deploy(self, project):
        project = api.projects.get(project)
        if not os.path.isfile(project.appconfig):
            raise ApiError("Project missing app.yaml file!")
        
        with open(project.appconfig) as f:
            config = yaml.load(f.read())
        
        # Check if the app.yaml has changed since the
        # last time we setup the project
        # TODO: do this
        #if os.path.isfile(project.appconfig_last):
        #    with open(project.appconfig_last) as f:
        #        rev = f.read()
        #        # check against repo
        #        # cd project; git-log -1 -- app.yaml | awk '/commit/ {print $2}'
        #
        
        # Simple counter to make unique names for each handler
        handler_position = 0
        vhost_sections = []
        for handler in config.get('handlers', []):
            if handler.get('worker'):
                # Setup worker
                name = '%s_%d' % (project.name, handler_position)
                handle = Handler(name, **handler)
                # write out start up scripts
                handle.write_supervisor_conf(project)
                handle.write_startup_script(project)
                # add handler to vhost_sections
                vhost_sections.append(handle)
                handler_position += 1
            else:
                # Just pass the dictionary to the proxy vhosts
                vhost_sections.append(handler)
        
        # Write out the proxy file to serve this app
        ctx = {
            'sections': vhost_sections,
            'domain': config.get('domain', project.default_domain),
            'runtime': config.get('runtime', 'python'),
            'port': config.get('port', 80)
        }
        write_file(project.vhost_conf, proxy.template, ctx)
                