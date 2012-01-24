import ConfigParser, os

config = ConfigParser.ConfigParser()
config.readfp(open('defaults.cfg'))

CANNULA_ETC_CONF = '/etc/cannula/cannula.conf'
CANNULA_HOME_CONF = os.path.expanduser('~/.cannula.conf')

config.read([CANNULA_ETC_CONF, CANNULA_HOME_CONF])


# Cannula settings
CANNULA_MODULE_DIR = os.path.abspath(os.path.dirname(__file__))
CANNULA_BASE = config.get('cannula', 'base')

# Proxy client, default options are:
CANNULA_PROXY_CMD = config.get('proxy', 'cmd')
CANNULA_PROXY_NEEDS_SUDO = config.getboolean('proxy', 'needs_sudo')

# Process Supervisor Settings
CANNULA_SUPERVISOR_USE_INET = config.getboolean('proc', 'use_inet')
CANNULA_SUPERVISOR_INET_PORT = config.get('proc', 'inet_port')
CANNULA_SUPERVISOR_USER = config.get('proc', 'user')
CANNULA_SUPERVISOR_PASSWORD = config.get('proc', 'password')
CANNULA_SUPERVISOR_MANAGES_PROXY = config.getboolean('proc', 'manages_proxy')

# Path to 'git' command
CANNULA_GIT_CMD = config.get('cannula', 'git_cmd') #reese

# Path to cannulactl command
CANNULA_CMD = config.get('cannula', 'cmd')
# Path to canner.sh bash script 
CANNULA_SSH_COMMAND = config.get('cannula', 'ssh_cmd')

# API classes you can override a single one in django settings
# this dictionary will be updated with the user defined one.
CANNULA_API = dict(config.items('api'))

# Lock timeout in seconds
CANNULA_LOCK_TIMEOUT = config.getint('cannula', 'lock_timeout')

def conf_dict():
    """Generate a configuration dict to use in a form."""
    sections = ['django', 'database', 'cannula', 'proxy', 'proc', 'api']
    configuration = {}
    for section in sections:
        for key, value in config.items(section):
            if value in ['True', 'False']:
                value = value.lower()
            configuration['%s_%s' % (section, key)] = value
    
    return configuration

def write_config(configuation):
    
    for key, value in configuation.items():
        # split the key (section_option) into section option
        section = key[:key.index('_')]
        option = key[key.index('_')+1:]
        config.set(section, option, value)
    
    # Figure out where to write this
    etc_conf = os.path.isfile(CANNULA_ETC_CONF)
    
    # Prefer home conf over etc if it exists
    conf = CANNULA_HOME_CONF
    if etc_conf:
        conf = CANNULA_ETC_CONF
    
    with open(conf, 'w') as fp:
        config.write(fp)