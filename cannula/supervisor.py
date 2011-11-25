import os
import logging
import xmlrpclib
import posixpath

from django.template.loader import render_to_string
from django.template.base import TemplateDoesNotExist

from cannula.conf import CANNULA_BASE, SUPERVISOR_PORT
from cannula.utils import shell

log = logging.getLogger("cannula.supervisor")

class Supervisor(object):
    
    main_conf_template = 'supervisor/supervisor_main.conf'
    template = 'supervisor/supervisor.conf'
    port = SUPERVISOR_PORT
    
    def __init__(self):
        self.server = xmlrpclib.Server(self.port)
        self.template_base = 'supervisor'
        self.context = {
            'cannula_base': CANNULA_BASE,
            'port': SUPERVISOR_PORT,
        }
    
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