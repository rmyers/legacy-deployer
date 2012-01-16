import os
import logging
import xmlrpclib
import posixpath

from supervisor.xmlrpc import SupervisorTransport

from django.template.loader import render_to_string

from cannula.conf import (CANNULA_BASE, CANNULA_SUPERVISOR_INET_PORT, 
    CANNULA_SUPERVISOR_USE_INET, CANNULA_SUPERVISOR_USER,
    CANNULA_SUPERVISOR_PASSWORD, CANNULA_SUPERVISOR_MANAGES_PROXY)
from cannula.utils import shell, Git, write_file
from cannula.api import api
from cannula.apis import Configurable


log = logging.getLogger("cannula.supervisor")

class Supervisord(Configurable):
    
    conf_type = 'proc'
    name = 'supervisor'
    cmd = 'supervisord'
    ctl_cmd = 'supervisorctl'
    extra_files = []
    main_conf_name = 'supervisor.conf'
    project_template = 'proc/supervisor/project.conf'
    
    
    def __init__(self):
        self.base = CANNULA_BASE
        self.supervisor_base = os.path.join(self.base, 'supervisor')
        self.socket_path = os.path.join(self.base, 'supervisor.sock')
        self.pid_file = os.path.join(self.base, 'supervisor.pid')
        self.socket = 'unix://%s' % self.socket_path
        self.username = CANNULA_SUPERVISOR_USER
        self.password = CANNULA_SUPERVISOR_PASSWORD
        self.use_inet = CANNULA_SUPERVISOR_USE_INET
        self.inet_port = CANNULA_SUPERVISOR_INET_PORT
        self.manages_proxy = CANNULA_SUPERVISOR_MANAGES_PROXY
        self.proxy = api.proxy if self.manages_proxy else None
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
            'manages_proxy': self.manages_proxy,
            'proxy': self.proxy,
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

    def stop(self, name):
        return self.server.supervisor.stopProcessGroup(name)
    
    def start(self, name):
        return self.server.supervisor.startProcessGroup(name)
    
    def restart(self, name):
        self.stop(name)
        self.start(name)
    
    def add_project(self, name):
        try:
            self.server.supervisor.addProcessGroup(name)
        except xmlrpclib.Fault, f:
            if f.faultCode == 90:
                log.warning("%s already added" % name)
            else:
                raise
    
    def startup(self):
        status, output = shell('%(cmd)s -c %(main_conf)s' % self.__dict__)
        if status > 0:
            raise Exception(output)
        
    def shutdown(self):
        status, output = shell('%(ctl_cmd)s -c %(main_conf)s shutdown' % self.__dict__)
        if status > 0:
            logging.error(output)
    
    def write_project_conf(self, project, extra_ctx):
        ctx = self.context.copy()
        ctx.update(extra_ctx)
        return write_file(project.supervisor_conf, self.project_template, ctx)
