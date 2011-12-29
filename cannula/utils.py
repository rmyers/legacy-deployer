"""
cannula Utilities
================

Various helper scripts for the cannula framework.
"""
import sys
import traceback
import re
from logging import getLogger
from subprocess import Popen, PIPE

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('cannula', 'templates'))

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

def shell(command, cwd=None):
    log.debug('SHELL: %s' % command)
    process = Popen(command.strip(), stdout=PIPE, stderr=PIPE, shell=True, cwd=cwd)
    stdout, stderr = process.communicate()
    status = process.returncode
    if status == 0:
        return status, stdout
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

def render_to_string(template, context):
    temp = env.get_template(template)
    return temp.render(**context)

def write_file(file_name, template, context=None):
    if context is None:
        context = {}
    
    log.info("Writing file: %s", file_name)
    with open(file_name, 'w') as f:
        temp = render_to_string(template, context)
        f.write(temp)
        f.close()
    
class Git:
    """
    Simple helper object for interacting with configration repos.
    
    CANNULA_BASE/proxy/
    CANNULA_BASE/supervisor/
    CANNULA_BASE/config/(project)/
    CANNULA_BASE/pb/(message type)/
    
    We store changes to the configs in git in order to allow rollbacks
    and to show history of changes, you know like in your code!
    """

    init = '%s init' % CANNULA_GIT_CMD
    add_all = '%s add --all' % CANNULA_GIT_CMD
    reset = '%s reset --hard' % CANNULA_GIT_CMD
    status = "%s status -s" % CANNULA_GIT_CMD
    new_files =  "%s status -s |awk '/A/ {print $2}'" % CANNULA_GIT_CMD
    modifed_files = "%s status -s |awk '/M/ {print $2}'" % CANNULA_GIT_CMD
    head = "%s log -1 --pretty=oneline |awk '{print $1}'" % CANNULA_GIT_CMD
    commit = '%s commit -m "%%s"' % CANNULA_GIT_CMD
    diff = '%s diff' % CANNULA_GIT_CMD
    push = '%s push %%s' % CANNULA_GIT_CMD