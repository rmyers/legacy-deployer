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

log = getLogger('cannula.utils')

def shell(command, cwd=None):
    log.debug('SHELL: %s' % command)
    process = Popen(command.strip(), stdout=PIPE, stderr=PIPE, shell=True, cwd=cwd)
    log.debug('SHELL PID: %d' % process.pid)
    stdout, stderr = process.communicate()
    log.debug('SHELL FINISHED COMMUNICATION')
    status = process.returncode
    if status == 0:
        return status, stdout
    else:
        return status, stderr


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
    
    