"""
## Cannula Runtimes

These define the way the runtimes for each application are created.
Currently only `cannula.runtimes.Python` is implemented. However
it would be easy to define a custom one for Ruby or Java if desired.

### Specifing Runtime to Use 

You specify the runtime in the application's `app.yaml` file like so

    domain: example.com
    version: 1.0
    runtime: cannula.runtime.Python
    api_version: 1
"""

import os
import sys

# click here: [[utils.py]]
from cannula.utils import call_subprocess

class Runtime(object):
    """###Base Runtime
    
    Subclasses should implement the `bootstrap` and `teardown` 
    methods.
    """
    
    @classmethod
    def notify(cls, message):
        """
        #### `notify(message)`
        
        Display a message to a user safely. The runtime code
        is actually run in a git command, so we need to use
        stderr to bubble the message up to the user.
        """
        sys.stderr.write('%s\n' % message)
        sys.stderr.flush()

    @classmethod
    def call(cls, cmd, cwd=None, env=None, status=0):
        """
        #### `call(cmd)`
        
        Call subprocess and check that the exit status matches
        the expected output. Pass `status=None` to allow ignore
        all errors. `cwd` specifies the directory to execute in
        otherwise the current dir is used. `env` allows you to 
        pass a dictionary of environment settings to use. 
        """
        st = call_subprocess(cmd, cwd, env)
        if status is None:
            return st
        if st != status:
            raise RuntimeError("Command Failed: %s" % cmd)
        return st
        
    @classmethod
    def bootstrap(cls, project, application):
        """
        #### `bootstrap(project, application)`
        
        Called to build the environment that will
        run the project.

        Arguments:

        * `project`: The project that is being pushed
        * `application`: The application 
        """
        raise NotImplementedError
    
    @classmethod
    def teardown(cls, project, application):
        """
        #### `teardown(project)`
        
        Called to destroy the environment for the project.

        Arguments:

        * `project`: The project that is being torn down.
        """
        if os.path.isdir(project.virtualenv):
            import shutil
            cls.notify("Removing env: %s" % project.virtualenv)
            shutil.rmtree(project.virtualenv)


class Python(Runtime):
    """### Python runtime setup and teardown.
    
    Initialize a virtual environment for this project.
    All python projects must include a `requirements.txt` file
    with all the dependancies.
    """
    
    @classmethod
    def bootstrap(cls, project, application):
        # The requirements file of the project that was pushed.
        requirements = os.path.join(project.project_dir, 'requirements.txt')
        if not os.path.isfile(requirements):
            raise Exception("Requirement file not found: %s" % requirements)
        
        py_version = application.get('python_version', sys.executable)
        
        cmd = 'virtualenv --distribute --python=%s %s'
        
        if not os.path.isdir(project.virtualenv):
            cls.notify("Creating virtual environment for %s" % project)
            cls.call(cmd % (py_version, project.virtualenv))
        
        pip = os.path.join(project.virtualenv, 'bin', 'pip')
        cls.notify("Installing requirements\n")
        
        cls.call("%s install -r %s" % (pip, requirements))
        
        