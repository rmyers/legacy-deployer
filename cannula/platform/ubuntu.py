
import posixpath
import datetime

from django.template.loader import render_to_string

from cannula.platform.posix import POSIX, PlatformError
from cannula.conf import api, config

BASE_DEPENDS = ['apache2', 'nginx', 'build-essential', 'python-setuptools']

class Ubuntu(POSIX):
    
    def bootstrap(self, channel, depends=[]):
        base = config.get('global', 'base')
        base_dir = posixpath.join(base, 'base')
        bin_dir = posixpath.join(base, 'bin')
        deps = set(BASE_DEPENDS)
        [deps.add(x) for x in depends]
        apt_depends = ' '.join(deps)
        self.mkdir(channel, base_dir)
        self.mkdir(channel, bin_dir)
        self.sudo(channel, '/usr/bin/apt-get install %s -y' % apt_depends)
    
    def make_init_script(self, channel, group, project, template=None):
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        base = config.get('global', 'base')
        base_dir = posixpath.join(base, 'base')
        bin_dir = posixpath.join(base, 'bin')
        ctx = {'group': group, 'project': project, 'bin_dir': bin_dir,
               'base_dir': base_dir, 'date': datetime.datetime.now()}
        if template is None:
            template = 'plaform/ubuntu/upstart.conf'
        proj_name = '%s.%s.conf' % (group.abbr, project.abbr)
        conf = render_to_string(template, ctx)
        self.put(channel, remote_path='/tmp/%s' % proj_name, content=conf)
        self.sudo(channel, '/bin/mv %s /etc/init/' % '/tmp/%s' % proj_name)
        self.sudo(channel, '/sbin/initctl reload-configuration')