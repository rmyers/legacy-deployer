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

try:
    from importlib import import_module
except ImportError:  # Compatibility for Python <= 2.6
    from django.utils.importlib import import_module

from django.forms.util import ValidationError
from django.contrib.admin.helpers import AdminForm
from django.template.loader import render_to_string

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