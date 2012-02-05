import os
import shutil
import logging
import yaml
import fcntl
import re
import datetime

from logging import getLogger

from django.db.models.loading import get_model

from cannula.apis import BaseAPI, ApiError
from cannula.api import api
from cannula import conf
from cannula.git import Git
from cannula.utils import import_object

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
    
    def _create(self, project, user, oldrev, newrev, conf_oldrev, conf_newrev):
        self.model.objects.create(project=project, user=user, oldrev=oldrev,
            newrev=newrev, conf_oldrev=conf_oldrev, conf_newrev=conf_newrev)
    
    def deploy(self, project, user, oldrev, newrev):
        user = api.users.get(user)
        project = api.projects.get(project)
        if not os.path.isfile(project.appconfig):
            raise ApiError("Project missing app.yaml file!")
        
        with open(project.appconfig) as f:
            # Attempt to get an exclusive lock on the app.yaml
            # file. A way to ensure only one process can deploy
            # at any single time. This is hard because deployment is
            # triggered by a git push (which is just an ssh connection)
            # TODO: Add test to verify this works/find reliable lock
            try:
                fcntl.flock(f, fcntl.LOCK_EX|os.O_NDELAY)
            except IOError:
                raise ApiError("Another person is deploying?")
            
            # Store the configuration for this project in git repo
            # so that we can roll back to previous states
            conf_dir = Git(project.conf_dir)
            
            if not os.path.isdir(project.conf_dir):
                os.makedirs(project.conf_dir)
                conf_dir.init()
                # Add an initial commit, just to make a rollback point.
                open(project.deployconfig, 'a')
                conf_dir.add_all()
                conf_dir.commit("Initial Commit")
            
            # Copy the project app.yaml to the conf_dir
            shutil.copy(project.appconfig, project.deployconfig)
            
            # read in the application configuration
            app = yaml.load(f.read())
            
            # setup any runtime specific things here
            try:
                runtime = import_object(app.get('runtime'))
            except ImportError:
                raise ApiError("Unsupported runtime!")
            # runtime bootstrap, setup project environment here
            runtime.bootstrap(project, app)    
                
        
            # Simple counter to make unique names for each handler
            # and keep them in order
            handler_position = 0
            sections = []
            for handler in app.get('handlers', []):
                if handler.get('worker'):
                    # Setup worker
                    name = '%s_%d' % (project.name, handler_position)
                    # defaults are special, they reference another
                    # section in the app.yaml
                    defaults = handler.pop('defaults', None)
                    if defaults:
                        handler_defaults = app.get(defaults, {})
                        handler.update(handler_defaults)
                    handle = Handler(name, project, **handler)
                    # write out bash start up scripts
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
                'domain': app.get('domain', 'localhost'),
                'runtime': app.get('runtime', 'python'),
                'port': app.get('port', 80),
                'project_conf_dir': project.conf_dir,
                'conf_dir': os.path.join(conf.CANNULA_BASE, 'config'),
                'project': project,
            }
            api.proxy.write_vhost_conf(project, ctx)
            api.proc.write_project_conf(project, ctx)
            
            # Check if any files changed and check if still valid
            conf_dir.add_all()
            _, changed = conf_dir.status()
            logging.debug(changed)
            if re.search('vhost.conf', changed):
                # Vhost file is either new or changed which will require 
                # our proxy server to reload its configuration files.
                try:
                    api.proxy.restart()
                except:
                    logging.exception("Error restarting proxy")
                    conf_dir.reset()
                    raise ApiError("Deployment failed")
            if re.search('supervisor.conf', changed):
                try:
                    api.proc.reread()
                except:
                    logging.exception("Error reading supervisor configs")
                    conf_dir.reset()
                    raise ApiError("Deployment failed")
            
            # Add the project
            api.proc.reread(stderr=True)
            api.proc.add_project(project.name)
                
            # Restart the project
            try:
                api.proc.restart(project.name, stderr=True)
            except:
                logging.exception("Error restarting project")
                conf_dir.reset()
                raise ApiError("Deployment failed")
            # Current revision of conf directory
            conf_oldrev = conf_dir.head()
            if changed:
                # Commit config changes
                conf_dir.commit("Configuration: %s" % datetime.datetime.now().ctime())
            
            # new revision of conf directory
            conf_newrev = conf_dir.head()
            if oldrev is None:
                oldrev = "Initial Commit"
            self._create(project, user, oldrev, newrev, conf_oldrev, conf_newrev)
            # finally release the lock
            fcntl.flock(f, fcntl.LOCK_UN)       