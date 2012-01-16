
import os

from cannula.utils import import_object

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
    
# Check for if Django settings module is defined.
if os.environ.get('DJANGO_SETTINGS_MODULE'):
    from django.conf import settings
else:
    class settings(object):
        pass
    
#if os.environ.get('CANNULA_SETTINGS_MODULE', None):
    #logging.info('Settings setup')
    #mod = os.environ['CANNULA_SETTINGS_MODULE']
    #config = ConfigParser()
    #config.read([mod])
    #for k, v in config.items('cannula'):
        #logging.info("Setting: %s: %s", k, v)
        #setattr(settings, k.upper(), v)
#else:
    #logging.info("No custom settings found")
    
#
# CANNULA DEFAULT SETTINGS
#

# Base directory where configuration files are placed.
# This must be writable by the user running cannula.
CANNULA_BASE = getattr(settings, 'CANNULA_BASE', '/tmp/cannula/')

# Proxy client, default options are:
#     'cannula.proxy.nginx'
#     'cannula.proxy.apache'
#     or roll your own and provide the dotted path here
CANNULA_PROXY_CMD = getattr(settings, 'CANNULA_PROXY', 'nginx')
CANNULA_PROXY_NEEDS_SUDO = getattr(settings, 'CANNULA_PROXY_NEEDS_SUDO', False)

# Process Supervisor Settings
CANNULA_SUPERVISOR = getattr(settings, 'CANNULA_SUPERVISOR', 'cannula.apis.v2.proc.supervisord')
CANNULA_SUPERVISOR_USE_INET = getattr(settings, 'CANNULA_SUPERVISOR_USE_INET', False)
CANNULA_SUPERVISOR_INET_PORT = getattr(settings, 'CANNULA_SUPERVIOR_INET_PORT', 'http://localhost:9001')
CANNULA_SUPERVISOR_USER = getattr(settings, 'CANNULA_SUPERVISOR_USER', 'watchman')
CANNULA_SUPERVISOR_PASSWORD = getattr(settings, 'CANNULA_SUPERVISOR_PASSWORD', 'ChangeMeBro!')
CANNULA_SUPERVISOR_MANAGES_PROXY = getattr(settings, 'CANNULA_SUPERVISOR_MANAGES_PROXY', True)

# Path to 'git' command
CANNULA_GIT_CMD = getattr(settings, 'CANNULA_GIT_CMD', 'git')

# Cannula admin command
_cannula_cmd = os.path.join(CURRENT_DIR, 'bin', 'admin.py')
CANNULA_CMD = getattr(settings, 'CANNULA_CMD', _cannula_cmd)

# API classes you can override a single one in django settings
# this dictionary will be updated with the user defined one.
CANNULA_API = {
    #'clusters': 'cannula.api.djangodb.clusters.ClusterAPI',
    'deploy': 'cannula.apis.v2.deploy.DeployAPI',
    'groups': 'cannula.apis.v2.groups.GroupAPI',
    'keys': 'cannula.apis.v2.keys.KeyAPI',
    'log': 'cannula.apis.v2.log.LoggingAPI',
    #'packages': 'cannula.api.djangodb.packages.PackageAPI',
    'permissions': 'cannula.apis.v2.permissions.PermissionAPI',
    'proc': 'cannula.apis.v2.proc.Supervisord',
    'projects': 'cannula.apis.v2.projects.ProjectAPI',
    'proxy': 'cannula.apis.v2.proxy.Nginx',
    #'servers': 'cannula.api.djangodb.servers.ServerAPI',
    #'unix_ids': 'cannula.api.djangodb.unix_id.UnixIDAPI',
    'users': 'cannula.apis.v2.users.UserAPI',
}
# Update the api with user specified Classes.
_api = getattr(settings, 'CANNULA_API', {})
CANNULA_API.update(_api)

# Lock timeout in seconds
CANNULA_LOCK_TIMEOUT = getattr(settings, 'CANNULA_LOCK_TIMEOUT', 30)


