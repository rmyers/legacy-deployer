import os
import sys
import logging
import xmlrpclib

from supervisor.xmlrpc import SupervisorTransport

from cannula import conf
from cannula.utils import shell, write_file
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
        self.base = conf.CANNULA_BASE
        self.supervisor_base = os.path.join(self.base, 'supervisor')
        self.socket_path = os.path.join(self.base, 'supervisor.sock')
        self.pid_file = os.path.join(self.base, 'supervisor.pid')
        self.socket = 'unix://%s' % self.socket_path
        self.username = conf.CANNULA_SUPERVISOR_USER
        self.password = conf.CANNULA_SUPERVISOR_PASSWORD
        self.use_inet = conf.CANNULA_SUPERVISOR_USE_INET
        self.inet_port = conf.CANNULA_SUPERVISOR_INET_PORT
        self.manages_proxy = conf.CANNULA_SUPERVISOR_MANAGES_PROXY
        self.proxy = api.proxy if self.manages_proxy else None
        self.serverurl = self.inet_port if self.use_inet else self.socket
        self.context = {
            'cmd': self.cmd,
            'ctl_cmd': self.ctl_cmd,
            'main_conf': self.main_conf,
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
    
    def reread(self, stderr=False):
        log.info("Reloading configuration")
        if stderr:
            sys.stderr.write("Supervisor --> reloading configuration\n")
        return self.server.supervisor.reloadConfig()

    def stop(self, name):
        log.info("Stopping: %s", name)
        return self.server.supervisor.stopProcessGroup(name)
    
    def start(self, name):
        log.info("Starting: %s", name)
        return self.server.supervisor.startProcessGroup(name)
    
    def restart(self, name, stderr=False):
        if stderr:
            sys.stderr.write("Supervisor --> restarting %s\n" % name)
        log.info("Restarting: %s", name)
        self.stop(name)
        self.start(name)
    
    def add_project(self, name, stderr=False):
        try:
            self.server.supervisor.addProcessGroup(name)
            log.info("Added group: %s", name)
        except xmlrpclib.Fault, f:
            if f.faultCode == 90:
                log.warning("%s already added" % name)
            else:
                raise
    
    def startup(self):
        status, output = shell('%(cmd)s -c %(main_conf)s' % self.context)
        if status > 0:
            raise Exception(output)
        
    def shutdown(self):
        status, output = shell('%(ctl_cmd)s -c %(main_conf)s shutdown' % self.context)
        if status > 0:
            logging.error(output)
    
    def write_project_conf(self, project, extra_ctx):
        ctx = self.context.copy()
        ctx.update(extra_ctx)
        return write_file(project.supervisor_conf, self.project_template, ctx)
