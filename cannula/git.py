
from cannula.conf import CANNULA_GIT_CMD
from cannula.utils import shell


class Git(object):
    """
    Simple wrapper for git command line utils.
    
    * CANNULA_BASE/proxy/
    * CANNULA_BASE/supervisor/
    * CANNULA_BASE/config/(project)/
    
    We store changes to the configs in git in order to allow rollbacks
    and to show history of changes, you know like in your code!
    """
    
    def __init__(self, directory):
        self.directory = directory
    
    def _exec(self, cmd, **kwargs):
        options = {'git': CANNULA_GIT_CMD}
        options.update(kwargs)
        return shell(cmd % options, cwd=self.directory)
    
    def init(self):
        return self._exec('%(git)s init')
    
    def add_all(self):
        return self._exec('%(git)s add --all')
    
    def reset(self, revision=''):
        return self._exec('%(git)s reset --hard %(revision)s', revision=revision)
    
    def new_files(self):
        return self._exec("%(git)s status -s |awk '/A/ {print $2}'")
    
    def modified_files(self):
        return self._exec("%(git)s status -s |awk '/M/ {print $2}'")
    
    def status(self):
        return self._exec('%(git)s status -s')
    
    def head(self):
        _, head = self._exec("%(git)s log -1 --pretty=oneline |awk '{print $1}'")
        return head
    
    def commit(self, message):
        return self._exec("%(git)s commit -m '%(message)s'", message=message)
    
    def diff(self):
        return self._exec("%(git)s diff")
    
    def push(self, location, branch="master"):
        return self._exec("%(git)s push %(location)s %(branch)s", location=location, branch=branch)
    
    