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
            uwsgi.conf
            ...
            gunicorn.conf
            ...
        apache/
            main.coonf
            ...
"""

import os
import posixpath

from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from cannula.conf import CANNULA_BASE

class Proxy(object):
    
    def __init__(self, base=CANNULA_BASE, name='base', 
                 template_base='proxy', default_vhost='localhost'):
        self.cannula_base = base
        self.name = name
        self.template_base = posixpath.join(template_base, self.name)
        self.default_vhost = default_vhost
        self.base = os.path.join(self.cannula_base, self.name)
        self.main_conf = os.path.join(self.base, '%s.conf' % self.name)
        self.vhost_base = os.path.join(self.base, 'vhosts')
    
    def write_file(self, filename, context, template=None):
        """
        Write file to the filesystem, if the template does not 
        exist fail silently. Otherwise write the file out and return
        boolean if the content had changed from last write. If the 
        file is new then return True.
        """
        if template is None:
            template = os.path.basename(filename)
        if '/' not in template:
            # template is not a full path, generate it now.
            template = posixpath.join(self.template_base, template)
        try:
            content = render_to_string(template, context)
        except TemplateDoesNotExist:
            return False
        
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename), mode=0750)
        
        original_content = ''
        if os.path.isfile(filename):
            with open(filename, 'rb') as file:
                original_content = file.read()
        
        with open(filename, 'wb') as file:
            file.write(content)
        
        return content != original_content

    
    def write_worker_conf(self, worker, deployment, context):
        name = "%s_%s.conf" % (deployment.project.group.abbr,
                               deployment.project.abbr)
        vhost = self.default_vhost
        if deployment.vhost:
            vhost = self.default_vhost
        filename = os.path.join(self.vhost_base, vhost, name)
        
        return self.write_file(filename, context, '%s.conf' % worker)
        
     
    def write_main_conf(self, context={}):
        return self.write_file(self.main_conf, context, 'main.conf')
    
    def write_vhost_conf(self, vhost, context={}):
        vhost_name = vhost.replace('.', '_') + '.conf'
        vhost_conf_file = os.path.join(self.vhost_base, vhost_name)
        
        return self.write_file(vhost_conf_file, context, 'vhost.conf')


apache = Proxy(name='apache')
nginx = Proxy(name='nginx')