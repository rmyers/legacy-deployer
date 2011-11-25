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
        self.context = {
            'cannula_base': self.cannula_base,
            'vhost_base': self.vhost_base,
        }
    
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
        return self.write_file(ctx, 'main.conf')
    
    def write_vhost_conf(self, extra_context={}):
        ctx = self.context.copy()
        ctx.update(extra_context)
        return self.write_file(ctx, 'vhost.conf')
        


apache = Proxy(name='apache')
nginx = Proxy(name='nginx')