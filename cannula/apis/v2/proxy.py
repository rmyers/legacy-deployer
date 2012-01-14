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

from cannula.conf import CANNULA_BASE, CANNULA_SUPERVISOR_MANAGES_PROXY, CANNULA_PROXY_NEEDS_SUDO
from cannula.utils import shell, Git, render_to_string, write_file

from cannula.api import api

class Proxy(object):
    
    name = ''
    extra_files = []
    start_cmd = 'echo "Proxy did not define start_cmd"'
    stop_cmd = 'echo "Proxy did not define stop_cmd"'
    restart_cmd = 'echo "Proxy did not define restart_cmd"'
    
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
            'cannula_base': CANNULA_BASE,
            'vhost_base': self.vhost_base,
            'supervisor_managed': self.supervisor_managed,
        }
    
    @property
    def manual_start_cmd(self):
        return self.start_cmd % self.__dict__
    
    def start(self):
        """Start the proxy service."""
        if self.supervisor_managed:
            return api.proc.start('proxy-server')
        
        # Else start the proxy manually
        code, output = shell(self.start_cmd % self.__dict__)
        if code != 0:
            raise Exception(output)
    
    def stop(self):
        """Stop the proxy service."""
        if self.api.supervisor_managed:
            return api.proc.stop('proxy-server')
        
        # Else stop the proxy manually
        code, output = shell(self.stop_cmd % self.__dict__)
        if code != 0:
            raise Exception(output)
        
    def restart(self):
        """Restart the proxy service."""
        if self.supervisor_managed:
            return api.proc.restart('proxy-server')
        
        # Else restart the proxy manually
        code, output = shell(self.restart_cmd % self.__dict__)
        if code != 0:
            raise Exception(output)
    
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
        except:
            return ''

        return content
    
    def write_extras(self, extra_context={}, initialized=False):
        """
        Write all of the extra files to the proxy_base configuration directory.
        If initialized is False just return a list of files that would be created.
        """
        ctx = self.context.copy()
        ctx.update(extra_context)
        
        to_commit = []
        
        for extra in self.extra_files:
            fname = os.path.join(self.proxy_base, extra)
            to_commit.append(fname)
            content = self.render_file(ctx, extra)
            if not initialized:
                continue
            
            # Write the file
            with open(fname, 'w') as conf_file:
                conf_file.write(content)
        
        return to_commit
            
        
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
        
        outmsg = ''
        
        if commit or dry_run:
            initialized = self.initialize(dry_run)
            files = self.write_extras(extra_context, initialized)
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
            if not output:
                # Bail early
                return '\n\nNo Changes Found\n'
            else:
                outmsg += '\n\nFiles Changed:\n %s\n%s\n' % (output, diff_out)
                
            if dry_run:
                shell(Git.reset, cwd=self.proxy_base)
                return outmsg
            
            # Commit the changes
            code, output = shell(Git.commit % msg, cwd=self.proxy_base)
            if code == 0:
                outmsg += '%s\n' % output
                return outmsg
            else:
                shell(Git.reset, cwd=self.proxy_base)
                outmsg += "Commit Failed: %s\n" % output
                return outmsg
        
        # Default just print the content    
        return content
        
    def write_vhost_conf(self, project, extra_context={}):
        ctx = self.context.copy()
        ctx.update(extra_context)
        template = posixpath.join(self.template_base, 'vhost.conf')
        return write_file(project.vhost_conf, template, ctx)
        

class Nginx(Proxy):
    
    name = 'nginx'
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
    # TODO: Find extra files to add
    extra_files = []
    start_cmd = '%(cmd)s -f %(main_conf)s -k start'
    stop_cmd = '%(cmd)s -f %(main_conf)s -k stop'
    restart_cmd = '%(cmd)s -f %(main_conf)s -k graceful'
    
nginx = Nginx(cmd='nginx')
apache = Apache(cmd='httpd')