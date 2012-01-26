import os
import sys
import shutil
import logging
import yaml
import fcntl
import re

from logging import getLogger

from django.db.models.loading import get_model

from cannula.apis import BaseAPI, ApiError
from cannula.api import api
from cannula import conf
from cannula.utils import write_file, shell, import_object, Git

log = getLogger('api')

class Handler(object):
    """Simple object to hold properties for wsgi handlers"""
    
    def __init__(self, name, project, worker='', **kwargs):
        self._worker_klass = import_object(worker)
        self._project = api.projects.get(project)
        self._worker_obj = self._worker_klass(name, self._project, **kwargs)
    
    def __getattr__(self, attr):
        return getattr(self._worker_obj, attr)
    
class DeployAPI(BaseAPI):
    
    model = get_model('cannula', 'deployment')
    
    # Command for interacting with conf repos
    git_add_cmd = '%s add --all' % conf.CANNULA_GIT_CMD
    git_reset = '%s reset --hard' % conf.CANNULA_GIT_CMD
    git_status = "%s status -s |awk '{print $2}'" % conf.CANNULA_GIT_CMD
    git_log = "%s log -1 |awl '/commit/ {print $2}'" % conf.CANNULA_GIT_CMD
    git_commit = '%s reset --hard' % conf.CANNULA_GIT_CMD
    
    def _create(self, project, user, oldrev, newrev, conf_oldrev, conf_newrev):
        self.model.objects.create(project=project, user=user, oldrev=oldrev,
            newrev=newrev, conf_oldrev=conf_oldrev, conf_newrev=conf_newrev)
    
    def deploy(self, project, user, oldrev=None, newrev=None):
        user = api.users.get(user)
        project = api.projects.get(project)
        if not os.path.isfile(project.appconfig):
            raise ApiError("Project missing app.yaml file!")
        
        if not os.path.isdir(project.conf_dir):
            os.makedirs(project.conf_dir)
            shell(Git.init, cwd=project.conf_dir)
        
        with open(project.appconfig) as f:
            # Attempt to get an exclusive lock on this file
            try:
                fcntl.flock(f, fcntl.LOCK_EX|os.O_NDELAY)
            except IOError:
                raise ApiError("Another person is deploying?")
            
            # Copy the project to the conf_dir and add any new files
            shutil.copy(project.appconfig, project.deployconfig)
            shell(self.git_add_cmd, cwd=project.conf_dir)
            _, changed = shell(self.git_status, cwd=project.conf_dir)
            
            if changed:
                # we have changes in app.yaml lets reset everything
                config = yaml.load(f.read())
            
                # Simple counter to make unique names for each handler
                handler_position = 0
                sections = []
                for handler in config.get('handlers', []):
                    if handler.get('worker'):
                        # Setup worker
                        name = '%s_%d' % (project.name, handler_position)
                        handle = Handler(name, project, **handler)
                        # write out start up scripts
                        handle.write_startup_script()
                        # add handler to vhost_sections
                        sections.append(handle)
                        handler_position += 1
                    else:
                        # Just pass the dictionary to the proxy vhosts
                        sections.append(handler)
                
                # Write out the proxy file to serve this app
                ctx = {
                    'sections': sections,
                    'domain': config.get('domain', 'localhost'),
                    'runtime': config.get('runtime', 'python'),
                    'port': config.get('port', 80),
                    'project_conf_dir': project.conf_dir,
                    'conf_dir': os.path.join(conf.CANNULA_BASE, 'config'),
                    'project': project,
                }
                api.proxy.write_vhost_conf(project, ctx)
                api.proc.write_project_conf(project, ctx)
                
                # Check if any files changed and check if still valid
                shell(self.git_add_cmd, cwd=project.conf_dir)
                _, changed = shell(self.git_status, cwd=project.conf_dir)
                logging.debug(changed)
                if re.search('vhost.conf', changed):
                    try:
                        api.proxy.restart()
                    except:
                        logging.exception("Error restarting proxy")
                        shell(self.git_reset, cwd=project.conf_dir)
                        raise ApiError("Deployment failed")
                if re.search('supervisor.conf', changed):
                    try:
                        api.proc.reread()
                    except:
                        logging.exception("Error reading supervisor configs")
                        shell(self.git_reset, cwd=project.conf_dir)
                        raise ApiError("Deployment failed")
                
                # Add the project
                api.proc.add_project(project.name)
                api.proc.reread()
                
            # Restart the project
            try:
                api.proc.restart(project.name)
            except:
                logging.exception("Error restarting project")
                shell(self.git_reset, cwd=project.conf_dir)
                raise ApiError("Deployment failed")
            # Current revision of conf directory
            _, conf_oldrev = shell(self.git_log, cwd=project.conf_dir)
            if changed:
                # Commit config changes
                shell(self.git_commit % user, cwd=project.conf_dir)
            
            # new revision of conf directory
            _, conf_newrev = shell(self.git_log, cwd=project.conf_dir)
            logging.info("Old Project commit: %s", conf_oldrev)
            logging.info("New Project commit: %s", conf_newrev)
            self._create(project, user, oldrev, newrev, conf_oldrev, conf_newrev)
            # finally release the lock
            fcntl.flock(f, fcntl.LOCK_UN)       