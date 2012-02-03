"""
cannula Utilities
================

Various helper scripts for the cannula framework.
"""
import sys
import posixpath
from logging import getLogger
from subprocess import Popen, PIPE, STDOUT

from django.template.loader import render_to_string

try:
    from importlib import import_module
except ImportError:  # Compatibility for Python <= 2.6

    def _resolve_name(name, package, level):
        """Return the absolute name of the module to be imported."""
        if not hasattr(package, 'rindex'):
            raise ValueError("'package' not set to a string")
        dot = len(package)
        for x in xrange(level, 1, -1):
            try:
                dot = package.rindex('.', 0, dot)
            except ValueError:
                raise ValueError("attempted relative import beyond top-level "
                                  "package")
        return "%s.%s" % (package[:dot], name)
    
    
    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        if name.startswith('.'):
            if not package:
                raise TypeError("relative imports require the 'package' argument")
            level = 0
            for character in name:
                if character != '.':
                    break
                level += 1
            name = _resolve_name(name[level:], package, level)
        __import__(name)
        return sys.modules[name]

# TODO: find a way to customize this
CANNULA_GIT_CMD = 'git'

log = getLogger(__name__)

def shell(command, cwd=None, env=None):
    """Simple shell command processing, """
    log.debug('SHELL: %s' % command)
    process = Popen(command.strip(), stdout=PIPE, stderr=PIPE, shell=True, cwd=cwd, env=env)
    stdout, stderr = process.communicate()
    status = process.returncode
    if status == 0:
        return status, stdout + stderr
    else:
        log.info('Shell returned a non-zero exit code: %s', status)
        return status, stderr + stdout


def shell_escape(text):
    """
    Escape the passed text for use in the shell (Bash).
    The output text will be enclosed in double quotes.
    """
    if not text:
        return '""'
    # We need to escape special characters for bash, and in
    # Python, two backslashes represent one literal backslash.
    # Escape backslashes first, otherwise you would end up escaping the
    # other special characters' escape backslash.
    text = text.replace("\\", "\\\\")
    text = text.replace("$", "\\$")
    text = text.replace("`", "\\`")
    text = text.replace('"', '\\"')
    return '"%s"' % text

def import_object(dotted_path):
    """
    Import an object from a dotted path string.

    If dotted_path contains no dots, then try to import and return a module.
    """
    if not dotted_path:
        raise ValueError('dotted_path must not be empty')
    parts = dotted_path.rsplit('.', 1)
    mod = import_module(parts[0])
    mod_only = len(parts) == 1
    if mod_only:
        return mod
    obj = getattr(mod, parts[1])
    return obj

def add_blank_choice(choices, force=False):
    """
    Prepend a blank choice to the passed choices list if it contains more than
    one choice.  Always add a blank choice if force=True.
    """
    if force or len(choices) > 1:
        choices = [("", "---------")] + choices
    return choices

#def render_to_string(template, context):
#    temp = env.get_template(template)
#    return temp.render(**context)

def write_file(file_name, template, context=None):
    if context is None:
        context = {}
    
    log.info("Writing file: %s", file_name)
    with open(file_name, 'w') as f:
        temp = render_to_string(template, context)
        f.write(temp)
        f.close()

def call_subprocess(cmd, cwd=None, env=None):
    """Call subprocess and print out stderr/stdout during processing."""
    
    log.debug("Running command %s" % cmd)

    try:
        proc = Popen(cmd.strip(), stderr=STDOUT, stdout=PIPE, shell=True, cwd=cwd, env=env)
    except:
        log.exception("Error while executing command %s" % cmd)
        raise
    
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.strip()
        sys.stderr.write(line+'\n')

    proc.wait()
    return proc.returncode

def multi_process(cmds, cwd=None, env=None):
    """
    Run multiple processes in parallel and report status when finished.
    You might want to make sure these commands don't hang otherwise I will never
    return ;)
    
    This is usefull to run a command on multple remote hosts (git push remote ...)
    """
    import time
    
    if not isinstance(cmds, (list, tuple)):
        cmds = [cmds]
    running_procs = []
    finished_procs = []
    for cmd in cmds:
        p = Popen(cmd.strip(), stderr=STDOUT, stdout=PIPE, shell=True, cwd=cwd, env=env)
        running_procs.append(p)
    
    while len(running_procs):
        for proc in running_procs:
            proc.poll()
            if proc.returncode is not None:
                finished_procs.append((proc.returncode, proc.stdout.read()))
                running_procs.remove(proc)
            time.sleep(.05)
    
    return finished_procs