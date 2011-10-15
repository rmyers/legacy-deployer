
import logging

from celery.task import task
from cannula.filesystem import FileSystem, Directory, File
from cannula.conf import config
from cannula.methods import (DeploymentMethod, DeploymentError,
                            InvalidAction, InvalidStatus)

CANNULA_ROOT = config.get('global', 'base')

logger = logging.getLogger('cannula.deploy')

class ModWSGIFiles(FileSystem):
    
    template_dir = "methods/apache/modwsgi"
    
    root = Directory(CANNULA_ROOT, name='')
    apache = Directory(parent='$root')
    apache_root_conf = File(parent='$apache', name='httpd.conf')
    apache_apps = Directory(parent='$apache', name='apps')
    apache_conf = File(parent='$apache_apps', name='$apache_conf_name', 
        template='apache_app.conf')
    wsgi = Directory(parent='$root')
    wsgi_file = File(parent='$wsgi', name='$wsgi_file_name', template='wsgi.py')
    
    @property
    def wsgi_file_name(self):
        return "%s.wsgi" % self.deployment_name   
    
    @property
    def apache_conf_name(self):
        return "%s.conf" % self.deployment_name 
    
class ModWSGI(DeploymentMethod):
    
    @classmethod
    def create_project(cls, *args, **kwargs):
        pass
    
    @classmethod
    def deploy_project(cls, deployment):
        """
        Deploy this project. Here are the steps:

        * Sync the Unix ID
        * export code locally and change perms to uid/gid
        * Tar it up.
        * put the code on server and untar it.
        * re-link to the new code folder.
        * regenerate wsgi file.
        * regenerate apache conf. (restart apache if needed)
        """
        context = {'some': 'args'}
        logger.debug("Who are you?")
        with ModWSGIFiles(deployment) as files:
            logger.debug(files.apache_conf_name)           
            files.sync(context)
            print files.apache_root_conf.content
        
    @classmethod
    def delete_deployment(cls, *args, **kwargs):
        print "deleted"
    
    @classmethod
    def modify_deployment(cls, *args, **kwargs):
        """Raises 'InvalidAction' and 'InvalidStatus'"""
        raise NotImplementedError
