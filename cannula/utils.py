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

def format_exception(exc_info=None):
    if not exc_info:
        exc_info = sys.exc_info()
    return '\n'.join(traceback.format_exception(*exc_info))

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

pkg_err = """\
Must be at least two characters long, be all lowercase, and start with an
alpha character.  Numbers are allowed anywhere except the first
character. Underscores are allowed anywhere except the first and last
characters, but are discouraged.  See the "Naming Conventions" section
of <a href="http://www.python.org/dev/peps/pep-0008/">PEP 8</a> for
more info."""

def validate_python_package_name(name, check_conflict=False):
    """
    A function to be used in form clean methods that checks if the passed name
    is a valid Python package name and conforms to Python's naming standards.
    Returns None if name is valid, and raises a ValidationError otherwise.

    If group is True, then check that the name does not conflict with a
    built-in module.
    """
    if len(name) < 2:
        raise ValidationError(pkg_err)
    if not re.match('^[a-z]', name):
        raise ValidationError(pkg_err)
    if not re.match('[a-z][a-z0-9_]*[a-z0-9]$', name):
        raise ValidationError(pkg_err)
    if check_conflict:
        try:
            import_object(name)
            raise ValidationError("Name conflicts with built-in module")
        except ImportError:
            pass

def make_admin_form(form):
    """
    Make a regular form an AdminForm, then we can use admin styles.
    Because form.as_* sucks and looks crappy!
    """
    if not hasattr(form, 'fieldsets'):
        form.fieldsets = (('', {'fields': [f for f in form.fields]}),)
    if not hasattr(form, 'prepopulated_fields'):
        form.prepopulated_fields = {}
    return AdminForm(form, form.fieldsets, form.prepopulated_fields)
