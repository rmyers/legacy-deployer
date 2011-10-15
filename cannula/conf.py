
import os

from cannula.utils import import_object, add_blank_choice

##### Defaults #####################################################
# Base directory where configuration files are placed.
# This must be writable by the user running cannula.
CANNULA_BASE = '/cannula/'
# Proxy client, default options are:
#     'cannula.proxy.nginx'
#     'cannula.proxy.apache'
#     or roll your own and provide the dotted path here
CANNULA_PROXY = 'cannula.proxy.nginx'
# VCS options by default all that are supported by pip
# http://pip.openplans.org/
CANNULA_VCS_ENABLED = ('svn', 'git', 'hg', 'bzr')
# Worker types enabled
CANNULA_WORKERS_ENABLED = ('uwsgi', 'gunicorn', 'fastcgi')
# Flavors (project types) enabled
CANNULA_FLAVORS_ENABLED = ('Django', 'Pylons', 'Paste', 'PHP')
# API classes you can override a single one in django settings
# this dictionary will be updated with the user defined one.
CANNULA_API = {
    'clusters': 'cannula.api.djangodb.clusters.ClusterAPI',
    'deployments': 'cannula.api.djangodb.deployments.DeploymentAPI',
    'groups': 'cannula.api.djangodb.groups.GroupAPI',
    'log': 'cannula.api.djangodb.log.LoggingAPI',
    'packages': 'cannula.api.djangodb.packages.PackageAPI',
    'permissions': 'cannula.api.djangodb.permissions.PermissionAPI',
    'projects': 'cannula.api.djangodb.projects.ProjectAPI',
    'servers': 'cannula.api.djangodb.servers.ServerAPI',
    'unix_ids': 'cannula.api.djangodb.unix_id.UnixIDAPI',
    'users': 'cannula.api.djangodb.users.UserAPI',
}
#
# Dictionary of values to pass to the context when
# deploying applications. 
# CANNUL_CLUSTER_DEFAULTS = {
#     'cluster_abbr': {'special_value': 'for this cluster'},
#     '__all__':  {'values': 'for all clusters'}
# }
CANNULA_CLUSTER_DEFAULTS = {}
#
# Lock timeout in seconds
CANNULA_LOCK_TIMEOUT = 30
#### END Defaults ###################################################

# Check for if Django settings module is defined.
if os.environ.get('DJANGO_SETTINGS_MODULE'):
    from django.conf import settings
    CANNULA_BASE = getattr(settings, 'CANNULA_BASE', CANNULA_BASE)
    CANNULA_PROXY = getattr(settings, 'CANNULA_PROXY', CANNULA_PROXY)
    CANNULA_VCS_ENABLED = getattr(settings, 'CANNULA_VCS_ENABLED', CANNULA_VCS_ENABLED)
    CANNULA_CLUSTER_DEFAULTS = getattr(settings, 'CANNULA_CLUSTER_DEFAULTS', CANNULA_CLUSTER_DEFAULTS)
    CANNULA_LOCK_TIMEOUT = getattr(settings, 'CANNULA_LOCK_TIMEOUT', CANNULA_LOCK_TIMEOUT)
    # Update the api with user specified Classes.
    _api = getattr(settings, 'CANNULA_BASE', {})
    CANNULA_API.update(_api)

# Make nicer choices for forms
_vcs_name = {
    'svn': 'Subversion',
    'git': 'Git',
    'hg': 'Mecurial',
    'bzr': 'Bazaar',
}

# TODO: need a registry system
VCS_CHOICES = add_blank_choice([(vcs, _vcs_name[vcs]) for vcs in CANNULA_VCS_ENABLED])
WORKER_CHOICES = add_blank_choice([(w, w) for w in CANNULA_WORKERS_ENABLED]) 
FLAVOR_CHOICES = add_blank_choice([(f.lower(), f) for f in CANNULA_FLAVORS_ENABLED])

# TODO: Delete these
METHOD_CHOICES = []
PACKAGE_CHOICES = []

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
    
    clusters = LazyAPI(CANNULA_API['clusters'])
    deployments = LazyAPI(CANNULA_API['deployments'])
    groups = LazyAPI(CANNULA_API['groups'])
    log = LazyAPI(CANNULA_API['log'])
    packages = LazyAPI(CANNULA_API['packages'])
    permissions = LazyAPI(CANNULA_API['permissions'])
    projects = LazyAPI(CANNULA_API['projects'])
    servers = LazyAPI(CANNULA_API['servers'])
    users = LazyAPI(CANNULA_API['users'])
    unix_ids = LazyAPI(CANNULA_API['unix_ids'])

    def __init__(self):
        self._defaults = ['unix_ids', 'packages', 'log', 
                          'servers', 'groups', 'clusters', 
                          'permissions', 'deployments', 'projects', 
                          'users']
        # Allow for user defined API for any option not found
        # in the defaults add it now.
        for option, value in CANNULA_API.iteritems():
            if option not in self._defaults:
                setattr(self, option, LazyAPI(value))
    

api = API()
proxy = import_object(CANNULA_PROXY)