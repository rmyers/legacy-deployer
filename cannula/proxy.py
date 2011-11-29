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

from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from cannula.conf import CANNULA_SUPERVISOR, CANNULA_BASE, CANNULA_SUPERVISOR_MANAGES_PROXY, CANNULA_PROXY_NEEDS_SUDO
from cannula.utils import shell, Git, import_object

# Stop circular imports!
supervisor = import_object(CANNULA_SUPERVISOR)

class Proxy(object):
    
    name = ''
    
    def __init__(self, template_base='proxy', cmd=''):
        self.proxy_base = os.path.join(CANNULA_BASE, 'proxy')
        self.template_base = posixpath.join(template_base, self.name)
        self.main_conf = os.path.join(self.proxy_base, '%s.conf' % self.name)
        self.vhost_base = os.path.join(CANNULA_BASE, 'config')
        if CANNULA_PROXY_NEEDS_SUDO:
            self.cmd = 'sudo %s' % cmd
        else:
            self.cmd = cmd
        self.supervisor_managed = CANNULA_SUPERVISOR_MANAGES_PROXY
        self.context = {
            'proxy_base': self.proxy_base,
            'vhost_base': self.vhost_base,
            'supervisor_managed': self.supervisor_managed,
        }
    
    def start(self):
        """Start the proxy service."""
        if self.supervisor_managed:
            return supervisor.start('proxy-server')
        return self.start_manually()
    
    def start_manually(self):
        """Start up the proxy manually."""
        raise NotImplementedError
    
    def stop(self):
        """Stop the proxy service."""
        if self.supervisor_managed:
            return supervisor.stop('proxy-server')
        return self.stop_manually()
    
    def stop_manually(self):
        """Stop up the proxy manually."""
        raise NotImplementedError
        
    def restart(self):
        """Restart the proxy service."""
        if self.supervisor_managed:
            return supervisor.restart('proxy-server')
        return self.restart_manually()
    
    def restart_manually(self):
        """Restart the proxy manually."""
        raise NotImplementedError
    
    def initialize(self, dry_run=False):
        """Create proxy base directory and run git init. Return True if it exists."""
        if os.path.isdir(self.proxy_base):
            return True
        
        if dry_run:
            return False
        os.makedirs(self.proxy_base)
        shell(Git.init, cwd=self.proxy_base)
        return True
    
    def render_file(self, context, template):
        """
        Render the config file from the templates.
        """
        if '/' not in template:
            # template is not a full path, generate it now.
            template = posixpath.join(self.template_base, template)
        try:
            content = render_to_string(template, context)
        except TemplateDoesNotExist:
            return ''

        return content
    
    def write_extras(self, extra_context={}, initialized=False):
        """
        Subclasses can define this if needed. Returns a list of files added.
        If initialized is False just return a list of files that would be created.
        """
        return []
        
    def write_main_conf(self, extra_context={}, commit=False, dry_run=False, msg='', **kwargs):
        """
        Write file to the filesystem, if the template does not 
        exist fail silently. Otherwise write the file out and return
        boolean if the content had changed from last write. If the 
        file is new then return True.
        """
        ctx = self.context.copy()
        ctx.update(extra_context)
        content = self.render_file(ctx, 'main.conf')
        
        if commit or dry_run:
            initialized = self.initialize(dry_run)
            files = self.write_extras(extra_context, dry_run)
            # If folder hasn't been initialized and we are doing a
            # dry run bail early and notify of all files which will
            # be created.
            if not initialized and dry_run:
                new = [self.proxy_base, self.main_conf] + files
                return 'New Files:\n\n%s\n' % '\n'.join(new)
            with open(self.main_conf, 'w') as conf:
                conf.write(content)
            
            # Generate diff 
            _, diff_out = shell(Git.diff, cwd=self.proxy_base)
            # Add all the files for either a commit or reset
            shell(Git.add_all, cwd=self.proxy_base)
            _, output = shell(Git.status, cwd=self.proxy_base)
            if dry_run:
                shell(Git.reset, cwd=self.proxy_base)
                if not output:
                    return '\n\nNo Changes Found\n'
                return '\n\nFiles Changed:\n %s\n%s' % (output, diff_out)
            
            # Commit the changes
            code, output = shell(Git.commit % msg, cwd=self.proxy_base)
            if code == 0:
                return output
            else:
                shell(Git.reset, cwd=self.proxy_base)
                return "Commit Failed: %s" % output
        
        # Default just print the content    
        return content
        
    def write_vhost_conf(self, extra_context={}):
        ctx = self.context.copy()
        ctx.update(extra_context)
        return self.write_file(ctx, 'vhost.conf')
        

class Nginx(Proxy):
    
    name = 'nginx'
    
    def write_extras(self, extra_context={}, initialized=False):
        # TODO: add mimetypes
        return []
    
    def start_manually(self):
        code, output = shell('%(cmd)s -c %(main_conf)s' % self.__dict__)
        if code != 0:
            raise Exception(output)
    
    def stop_manually(self):
        code, output = shell('%(cmd)s -c %(main_conf)s -s stop' % self.__dict__)
        if code != 0:
            raise Exception(output)
    
    def restart_manually(self):
        code, output = shell('%(cmd)s -c %(main_conf)s -s reload' % self.__dict__)
        if code != 0:
            raise Exception(output)
 
class Apache(Proxy):
    
    name = 'apache'
    
    def write_extras(self, extra_context={}, initialized=False):
        # TODO: add mimetypes
        return []
    
    def start_manually(self):
        code, output = shell('%(cmd)s -f %(main_conf)s -k start' % self.__dict__)
        if code != 0:
            raise Exception(output)
    
    def stop_manually(self):
        code, output = shell('%(cmd)s -f %(main_conf)s -k stop' % self.__dict__)
        if code != 0:
            raise Exception(output)
    
    def restart_manually(self):
        code, output = shell('%(cmd)s -f %(main_conf)s -k graceful' % self.__dict__)
        if code != 0:
            raise Exception(output)
    
    
nginx = Nginx(cmd='nginx')
apache = Apache(cmd='httpd')