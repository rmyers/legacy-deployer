import os
import sys
import yaml
import fcntl

from logging import getLogger

from django.db.models.loading import get_model

from cannula.api import BaseAPI, ApiError
from cannula.conf import api, proxy, CANNULA_GIT_CMD
from cannula.utils import write_file, shell, import_object
import shutil

log = getLogger('api')

class Handler(object):
    """Simple object to hold properties for wsgi handlers"""
    
    def __init__(self, name, worker, **kwargs):
        self._worker_klass = import_object(worker)
        self._worker_obj = self._worker_klass(name, **kwargs)
    
    def __getattr__(self, attr):
        return getattr(self._worker_obj, attr)
    
class DeployAPI(BaseAPI):
    
    git_add_cmd = '%s add --all' % CANNULA_GIT_CMD
    appyaml_status = "%s status -s |awk '/app.yaml/ {print $2}'" % CANNULA_GIT_CMD
    
    def deploy(self, project):
        project = api.projects.get(project)
        if not os.path.isfile(project.appconfig):
            raise ApiError("Project missing app.yaml file!")
        
        with open(project.appconfig) as f:
            # Attempt to get an exclusive lock on this file
            try:
                fcntl.flock(f, fcntl.LOCK_EX|os.O_NDELAY)
            except IOError:
                raise ApiError("Another person is deploying?")
            
            # Copy the project to the conf_root and add any new files
            shutil.copy(project.appconfig, project.deployconfig)
            shell(self.git_add_cmd, cwd=project.conf_root)
            _, changed = shell(self.appyaml_status, cwd=project.conf_root)
            
            if changed:
                # we have changes in app.yaml lets reset everything
                config = yaml.load(f.read())
            
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
            
            # finally release the lock
            fcntl.flock(f, fcntl.LOCK_UN)    