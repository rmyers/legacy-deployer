import os
import logging
import xmlrpclib

from cannula.conf import CANNULA_BASE, SUPERVISOR_PORT
from cannula.utils import shell

log = logging.getLogger("cannula.supervisor")

class Supervisor(object):
    
    template = 'supervisor/supervisor.conf'
    port = SUPERVISOR_PORT
    
    def __init__(self):
        self.server = xmlrpclib.Server(self.port)
    
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
    
    