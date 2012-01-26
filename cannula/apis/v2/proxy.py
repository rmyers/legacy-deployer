"""
Proxy handlers 
==============

These define the how the proxy are setup. The simplest proxies
should only need to define the 'name' and optionally the 
'template_base' attributes. All the magic is handled by the
templates. The templates are arranged like this::

    proxy/
        nginx/
            main.conf
            vhost.conf
            ...
        apache/
            main.conf
            vhost.conf
            ...
"""

import os
import posixpath

from cannula.conf import CANNULA_BASE, CANNULA_SUPERVISOR_MANAGES_PROXY, CANNULA_PROXY_NEEDS_SUDO,\
    CANNULA_PROXY_CMD
from cannula.utils import shell, write_file

from cannula.api import api
from cannula.apis import Configurable

class Proxy(Configurable):
    
    conf_type = 'proxy'
    name = ''
    extra_files = []
    start_cmd = 'echo "Proxy did not define start_cmd"'
    stop_cmd = 'echo "Proxy did not define stop_cmd"'
    restart_cmd = 'echo "Proxy did not define restart_cmd"'
    
    def __init__(self, template_base='proxy'):
        self.cmd = CANNULA_PROXY_CMD
        self.proxy_base = os.path.join(CANNULA_BASE, 'proxy')
        self.vhost_base = os.path.join(CANNULA_BASE, 'config')
        if CANNULA_PROXY_NEEDS_SUDO:
            self.cmd = 'sudo %s' % self.cmd
        self.supervisor_managed = CANNULA_SUPERVISOR_MANAGES_PROXY
        self.context = {
            'cmd': self.cmd,
            'main_conf': self.main_conf,
            'proxy_base': self.proxy_base,
            'cannula_base': CANNULA_BASE,
            'vhost_base': self.vhost_base,
            'supervisor_managed': self.supervisor_managed,
        }
    
    @property
    def manual_start_cmd(self):
        return self.start_cmd % self.context
    
    def start(self):
        """Start the proxy service."""
        if self.supervisor_managed:
            return api.proc.start('proxy-server')
        
        # Else start the proxy manually
        code, output = shell(self.start_cmd % self.context)
        if code != 0:
            raise Exception(output)
    
    def stop(self):
        """Stop the proxy service."""
        if self.api.supervisor_managed:
            return api.proc.stop('proxy-server')
        
        # Else stop the proxy manually
        code, output = shell(self.stop_cmd % self.context)
        if code != 0:
            raise Exception(output)
        
    def restart(self):
        """Restart the proxy service."""
        if self.supervisor_managed:
            return api.proc.restart('proxy-server')
        
        # Else restart the proxy manually
        code, output = shell(self.restart_cmd % self.context)
        if code != 0:
            raise Exception(output)
        
    def write_vhost_conf(self, project, extra_context={}):
        ctx = self.context.copy()
        ctx.update(extra_context)
        template = posixpath.join(self.template_base, 'vhost.conf')
        return write_file(project.vhost_conf, template, ctx)
        

class Nginx(Proxy):
    
    name = 'nginx'
    main_conf_name = 'nginx.conf'
    extra_files = [
        'mime.types',
        'fastcgi_params',
        'scgi_params',
        'uwsgi_params',
        'win-utf',
    ]
    start_cmd = '%(cmd)s -c %(main_conf)s'
    stop_cmd = '%(cmd)s -c %(main_conf)s -s stop'
    restart_cmd = '%(cmd)s -c %(main_conf)s -s reload'
 
class Apache(Proxy):
    
    name = 'apache'
    main_conf_name = 'httpd.conf'
    # TODO: Find extra files to add
    extra_files = []
    start_cmd = '%(cmd)s -f %(main_conf)s -k start'
    stop_cmd = '%(cmd)s -f %(main_conf)s -k stop'
    restart_cmd = '%(cmd)s -f %(main_conf)s -k graceful'
    