import os

from cannula import conf
from cannula.utils import shell, shell_escape

# TODO: wire up using different users
useradd_cmd = '/usr/sbin/useradd %(options)s %(name)s'
userdel_cmd = '/usr/sbin/userdel -r %(name)s'
userget_cmd = '/bin/grep ^%(name)s: /etc/passwd'

# TODO: Add a template directory for hooks
# git_init_cmd = '%(git_cmd)s init --bare --template %(template_dir)s %(repo)s'
git_init_cmd = '%(git_cmd)s init --bare --template %(template_dir)s %(repo)s'

def make_project(name, group):
    """
    Utility to create a project on the filesystem.
    
    #. Create a unix user for the project.
    #. Create home directory for code.
    #. Create a bare git repository for code.
    
    """
    # TODO: Check if user exists.
    # TODO: Create unix user.
    
    repo_dir = os.path.join(conf.CANNULA_BASE, group, '%s.git' % name)
    if not os.path.isdir(repo_dir):
        os.makedirs(repo_dir)
    
    project_dir = os.path.join(conf.CANNULA_BASE, group, name)
    if not os.path.isdir(project_dir):
        os.makedirs(project_dir)
    
    # TODO: find a way to locate the git templates in Django
    # Create the git repo
    args = {
        'git_cmd': conf.CANNULA_GIT_CMD,
        'template_dir': conf.CANNULA_GIT_TEMPLATES,
        'repo': name
    }
    shell(git_init_cmd % args)