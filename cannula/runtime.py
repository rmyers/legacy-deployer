import os
import sys

from cannula import conf
from cannula.utils import shell

class Runtime(object):
    """Base Runtime"""
    
    @classmethod
    def bootstrap(cls, project, application):
        """Setup any runtime specific things"""
        raise NotImplementedError
    
    @classmethod
    def teardown(cls, project, application):
        raise NotImplementedError

class Python(object):
    """Python runtime setup and teardown."""
    
    @classmethod
    def bootstrap(cls, project, application):
        """
        Initialize a virtual environment for this project.
        
        Looks for a 'requirements.txt' file for packages to install.
        """
        
        requirements = os.path.join(project.project_dir, 'requirements.txt')
        if not os.path.isfile(requirements):
            raise Exception("Requirement file not found: %s" % requirements)
        
        py_version = application.get('python_version', sys.executable)
        
        cmd = 'virtualenv --no-site-packages --distribute --python=%s %s'
        
        if not os.path.isdir(project.virtualenv):
            # write to std error cause then git-recieve-pack prints it out.
            # TODO: find a better way
            sys.stderr.write("Creating virtual environment for %s\n" % project)
            status, _ = shell(cmd % (py_version, project.virtualenv))
            if status > 0:
                raise Exception("Creating virtual environment failed: %s" % cmd)
        
        pip = os.path.join(project.virtualenv, 'bin', 'pip')
        sys.stderr.write("Installing requirements\n")
        
        status, output = shell("%s install -r %s" % (pip, requirements))
        if status > 0:
            raise Exception("Running pip failed: %s" % output)
        
        