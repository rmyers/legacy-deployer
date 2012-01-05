import os
import logging
import xmlrpclib
import posixpath

from supervisor.xmlrpc import SupervisorTransport

from cannula.conf import (CANNULA_BASE, CANNULA_SUPERVISOR_INET_PORT, 
    CANNULA_SUPERVISOR_USE_INET, CANNULA_SUPERVISOR_USER,
    CANNULA_SUPERVISOR_PASSWORD)
from cannula.utils import shell, render_to_string, Git

log = logging.getLogger("cannula.supervisor")

class Supervisord(object):
    
    name = ''
    extra_files = []
    main_conf_template = 'supervisor/supervisor_main.conf'
    template = 'supervisor/supervisor.conf'
    
    def __init__(self, cmd='supervisord', ctl_cmd='supervisorctl'):
        self.template_base = 'supervisor'
        self.cmd = cmd
        self.ctl_cmd = ctl_cmd
        self.base = CANNULA_BASE
        self.supervisor_base = os.path.join(self.base, 'supervisor')
        self.main_conf = os.path.join(self.supervisor_base, 'supervisor.conf')
        self.socket_path = os.path.join(self.base, 'supervisor.sock')
        self.pid_file = os.path.join(self.base, 'supervisor.pid')
        self.socket = 'unix://%s' % self.socket_path
        self.username = CANNULA_SUPERVISOR_USER
        self.password = CANNULA_SUPERVISOR_PASSWORD
        self.use_inet = CANNULA_SUPERVISOR_USE_INET
        self.inet_port = CANNULA_SUPERVISOR_INET_PORT
        self.serverurl = self.inet_port if self.use_inet else self.socket
        self.context = {
            'cannula_base': self.base,
            'inet_port': self.inet_port,
            'serverurl': self.serverurl,
            'use_inet_port': self.use_inet,
            'http_user': self.username,
            'http_password': self.password,
            'supervisor_sock': self.socket,
            'socket_path': self.socket_path,
        }
        # Setup the connection to the xmlrpc backend
        # xmlrpclib forces you to use an http uri, the SupervisorTransport
        # handles unix sockets as well as usernames and passwords.
        self.server = xmlrpclib.ServerProxy('http://127.0.0.1',
            transport=SupervisorTransport(
                username=self.username,
                password=self.password,
                serverurl=self.serverurl
            )
        )
    
    def reread(self):
        return self.server.supervisor.reloadConfig()

    def stop(self, project):
        return self.server.supervisor.stopProcessGroup(project.name)
    
    def start(self, project):
        return self.server.supervisor.startProcessGroup(project.name)
    
    def restart(self, project):
        self.stop(project)
        self.start(project)
    
    def add_project(self, project):
        try:
            self.server.supervisor.addProcessGroup(project.name)
        except xmlrpclib.Fault, f:
            if f.faultCode == 90:
                log.warning("%s already added" % project.name)
            else:
                raise
    
    def startup(self):
        shell('%(cmd)s -c %(main_conf)s -p %(pid_file)s' % self.__dict__)
    
    def shutdown(self):
        shell('%(ctl_cmd)s -c %(main_conf)s shutdown' % self.__dict__)
    
    def initialize(self, dry_run=False):
        """Create proxy base directory and run git init. Return True if it exists."""
        if os.path.isdir(self.supervisor_base):
            return True
        
        if dry_run:
            return False
        os.makedirs(self.supervisor_base)
        shell(Git.init, cwd=self.supervisor_base)
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
        Write all of the extra files to the supervisor_base configuration directory.
        If initialized is False just return a list of files that would be created.
        """
        ctx = self.context.copy()
        ctx.update(extra_context)
        
        to_commit = []
        
        for extra in self.extra_files:
            fname = os.path.join(self.supervisor_base, extra)
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
        content = self.render_file(ctx, self.main_conf_template)
        
        outmsg = ''
        
        if commit or dry_run:
            initialized = self.initialize(dry_run)
            files = self.write_extras(extra_context, initialized)
            # If folder hasn't been initialized and we are doing a
            # dry run bail early and notify of all files which will
            # be created.
            if not initialized and dry_run:
                new = [self.supervisor_base, self.main_conf] + files
                return 'New Files:\n\n%s\n' % '\n'.join(new)
            with open(self.main_conf, 'w') as conf:
                conf.write(content)
            
            # Generate diff 
            _, diff_out = shell(Git.diff, cwd=self.supervisor_base)
            # Add all the files for either a commit or reset
            shell(Git.add_all, cwd=self.supervisor_base)
            _, output = shell(Git.status, cwd=self.supervisor_base)
            if not output:
                # Bail early
                return '\n\nNo Changes Found\n'
            else:
                outmsg += '\n\nFiles Changed:\n %s\n%s\n' % (output, diff_out)
                
            if dry_run:
                shell(Git.reset, cwd=self.supervisor_base)
                return outmsg
            
            # Commit the changes
            code, output = shell(Git.commit % msg, cwd=self.supervisor_base)
            if code == 0:
                outmsg += '%s\n' % output
                return outmsg
            else:
                shell(Git.reset, cwd=self.supervisor_base)
                outmsg += "Commit Failed: %s\n" % output
                return outmsg
        
        # Default just print the content    
        return content
    
    def write_file(self, context, template):
        """
        Write file to the filesystem, if the template does not 
        exist fail silently. Otherwise write the file out and return
        boolean if the content had changed from last write. If the 
        file is new then return True.
        """
        if '/' not in template:
            # template is not a full path, generate it now.
            template = posixpath.join(self.template_base, template)
        
        content = render_to_string(template, context)
        
        return content

supervisord = Supervisord()