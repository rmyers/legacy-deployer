import os
import sys
import yaml

from logging import getLogger

from django.db.models.loading import get_model

from cannula.api import BaseAPI, ApiError
from cannula.conf import api, proxy, CANNULA_GIT_CMD
from cannula.utils import write_file, shell

log = getLogger('api')

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
        
                