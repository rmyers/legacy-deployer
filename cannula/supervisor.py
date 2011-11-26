import os
import logging
import xmlrpclib
import posixpath

from supervisor.xmlrpc import SupervisorTransport

from django.template.loader import render_to_string
from django.template.base import TemplateDoesNotExist

from cannula.conf import (CANNULA_BASE, CANNULA_SUPERVISOR_INET_PORT, 
    CANNULA_SUPERVISOR_USE_INET, CANNULA_SUPERVISOR_USER,
    CANNULA_SUPERVISOR_PASSWORD)
from cannula.utils import shell

log = logging.getLogger("cannula.supervisor")

class Supervisor(object):
    
    main_conf_template = 'supervisor/supervisor_main.conf'
    template = 'supervisor/supervisor.conf'
    
    def __init__(self):
        self.template_base = 'supervisor'
        self.base = CANNULA_BASE
        self.socket = os.path.join(self.base, 'supervisor.sock')
        self.username = CANNULA_SUPERVISOR_USER
        self.password = CANNULA_SUPERVISOR_PASSWORD
        self.use_inet = CANNULA_SUPERVISOR_USE_INET
        self.inet_port = CANNULA_SUPERVISOR_INET_PORT
        self.serverurl = self.inet_port if self.use_inet else self.socket
        self.context = {
            'cannula_base': self.base,
            'inet_port': self.inet_port,
            'use_inet_port': self.use_inet,
            'http_user': self.username,
            'http_password': self.password,
            'supervisor_sock': self.socket,
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
        shell('%(cmd)s -c %(base_conf)s -p %(pid_file)s' % self.__dict__)
    
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
        try:
            content = render_to_string(template, context)
        except TemplateDoesNotExist:
            return ''
        
        return content
     
    def write_main_conf(self, extra_context={}):
        ctx = self.context.copy()
        ctx.update(extra_context)
        return self.write_file(ctx, self.main_conf_template)

supervisor = Supervisor()