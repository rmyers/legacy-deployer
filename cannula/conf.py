
import os

from cannula.utils import import_object

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

##### Defaults #####################################################
# Base directory where configuration files are placed.
# This must be writable by the user running cannula.
CANNULA_BASE = '/cannula/'
# Proxy client, default options are:
#     'cannula.proxy.nginx'
#     'cannula.proxy.apache'
#     or roll your own and provide the dotted path here
CANNULA_PROXY = 'cannula.proxy.nginx'
# Path to 'git' command
CANNULA_GIT_CMD = 'git'
CANNULA_GIT_TEMPLATES = os.path.join(CURRENT_DIR, 'templates', 'git')
# Worker types enabled
CANNULA_WORKER = 'gunicorn'
# API classes you can override a single one in django settings
# this dictionary will be updated with the user defined one.
CANNULA_API = {
    #'clusters': 'cannula.api.djangodb.clusters.ClusterAPI',
    #'deployments': 'cannula.api.djangodb.deployments.DeploymentAPI',
    'groups': 'cannula.api.v2.groups.GroupAPI',
    'log': 'cannula.api.v2.log.LoggingAPI',
    #'packages': 'cannula.api.djangodb.packages.PackageAPI',
    #'permissions': 'cannula.api.djangodb.permissions.PermissionAPI',
    'projects': 'cannula.api.v2.projects.ProjectAPI',
    #'servers': 'cannula.api.djangodb.servers.ServerAPI',
    #'unix_ids': 'cannula.api.djangodb.unix_id.UnixIDAPI',
    'users': 'cannula.api.v2.users.UserAPI',
}
#
# Lock timeout in seconds
CANNULA_LOCK_TIMEOUT = 30
#### END Defaults ###################################################

# Check for if Django settings module is defined.
if os.environ.get('DJANGO_SETTINGS_MODULE'):
    from django.conf import settings
    CANNULA_BASE = getattr(settings, 'CANNULA_BASE', CANNULA_BASE)
    CANNULA_PROXY = getattr(settings, 'CANNULA_PROXY', CANNULA_PROXY)
    CANNULA_GIT_CMD = getattr(settings, 'CANNULA_GIT_CMD', CANNULA_GIT_CMD)
    CANNULA_GIT_TEMPLATES = getattr(settings, 'CANNULA_GIT_TEMPLATES', CANNULA_GIT_TEMPLATES)
    CANNULA_LOCK_TIMEOUT = getattr(settings, 'CANNULA_LOCK_TIMEOUT', CANNULA_LOCK_TIMEOUT)
    # Update the api with user specified Classes.
    _api = getattr(settings, 'CANNULA_API', {})
    CANNULA_API.update(_api)

class LazyAPI(object):
    
    def __init__(self, dotted_path):
        self._dotted_path = dotted_path
        self._api = None
    
    def __getattr__(self, attr):
        if not self._api:
            klass = import_object(self._dotted_path)
            self._api = klass()
        return getattr(self._api, attr)
    
class API:
    
    #clusters = LazyAPI(CANNULA_API['clusters'])
    #deployments = LazyAPI(CANNULA_API['deployments'])
    groups = LazyAPI(CANNULA_API['groups'])
    log = LazyAPI(CANNULA_API['log'])
    #packages = LazyAPI(CANNULA_API['packages'])
    #permissions = LazyAPI(CANNULA_API['permissions'])
    projects = LazyAPI(CANNULA_API['projects'])
    #servers = LazyAPI(CANNULA_API['servers'])
    users = LazyAPI(CANNULA_API['users'])
    #unix_ids = LazyAPI(CANNULA_API['unix_ids'])

    def __init__(self):
        self._defaults = ['log', 'groups',  'projects', 'users']
        # Allow for user defined API for any option not found
        # in the defaults add it now.
        for option, value in CANNULA_API.iteritems():
            if option not in self._defaults:
                setattr(self, option, LazyAPI(value))
    

api = API()
proxy = import_object(CANNULA_PROXY)

#TODO: delete these 
WORKER_CHOICES = []
VCS_CHOICES = []