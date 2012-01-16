
import os
import posixpath

from django.template.loader import render_to_string

from exceptions import ApiError
from exceptions import PermissionError
from exceptions import UnitDoesNotExist
from exceptions import DuplicateObject
from cannula.conf import CANNULA_BASE
from cannula.git import Git

class BaseAPI(object):
    
    model = None
    lookup_field = 'name'
    
    def get_object(self, name):
        """Get an object by the default lookup field name. Should be unique."""
        if isinstance(name, self.model):
            return name
        kwargs = {self.lookup_field: name}
        return self.model.objects.get(**kwargs)
    
    def get(self, name):
        try:
            return self.get_object(name)
        except self.model.DoesNotExist:
            raise UnitDoesNotExist
    
    def _send(self, *args, **kwargs):
        """Send a command to the remote cannula server."""

class Configurable(object):
    """
    Configurable mixin, for api objects that have configuration
    files that need to be written for projects.
    """
    
    conf_type = ''
    name = ''
    cmd = ''
    extra_files = []
    context = {}
    main_conf_template = 'main.conf'
    main_conf_name = 'main.conf'
    
    @property
    def git_repo(self):
        return Git(self.conf_base)
    
    @property
    def conf_base(self):
        return os.path.join(CANNULA_BASE, self.conf_type)
    
    @property
    def template_base(self):
        return os.path.join(self.conf_type, self.name)
    
    @property
    def main_conf(self):
        return os.path.join(self.conf_base, self.main_conf_name)
    
    def initialize(self, dry_run=False):
        """Create conf base directory and run git init. Return True if it exists."""
        if os.path.isdir(self.conf_base):
            return True
        
        if dry_run:
            return False
        os.makedirs(self.conf_base)
        status, out = self.git_repo.init()
        if status > 0:
            raise ApiError(out)
        return True
    
    def render_file(self, template, context):
        """
        Render the config file from the templates.
        """
        if '/' not in template:
            # template is not a full path, generate it now.
            template = posixpath.join(self.template_base, template)

        return render_to_string(template, context)
    
    def write_extras(self, extra_context={}, initialized=False):
        """
        Write all of the extra files to the conf_base configuration directory.
        If initialized is False just return a list of files that would be created.
        """
        ctx = self.context.copy()
        ctx.update(extra_context)
        
        to_commit = []
        
        for extra in self.extra_files:
            fname = os.path.join(self.conf_base, extra)
            to_commit.append(fname)
            content = self.render_file(extra, ctx)
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
        content = self.render_file(self.main_conf_template, ctx)
        
        outmsg = ''
        
        if commit or dry_run:
            initialized = self.initialize(dry_run)
            files = self.write_extras(extra_context, initialized)
            # If folder hasn't been initialized and we are doing a
            # dry run bail early and notify of all files which will
            # be created.
            if not initialized and dry_run:
                new = [self.conf_base, self.main_conf] + files
                return 'New Files:\n\n%s\n' % '\n'.join(new)
            with open(self.main_conf, 'w') as conf:
                conf.write(content)
            
            # Generate diff 
            _, diff_out = self.git_repo.diff()
            # Add all the files for either a commit or reset
            self.git_repo.add_all()
            _, output = self.git_repo.status()
            if not output:
                # Bail early
                return '\n\nNo Changes Found\n'
            else:
                outmsg += '\n\nFiles Changed:\n %s\n%s\n' % (output, diff_out)
                
            if dry_run:
                self.git_repo.reset()
                return outmsg
            
            # Commit the changes
            code, output = self.git_repo.commit(msg)
            if code == 0:
                outmsg += '%s\n' % output
                return outmsg
            else:
                self.git_repo.reset()
                outmsg += "Commit Failed: %s\n" % output
                return outmsg
        
        # Default just print the content    
        return content