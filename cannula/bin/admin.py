#!/usr/bin/env python
"""\
%prog [options] cmd

Run cron jobs for cannula.

Available commands:

* authorized_keys: Write out authorized_keys file
* initialize: Setup or reconfigure cannula

"""
import os
import sys
import logging

from optparse import OptionParser
from random import choice

def keys(commit=False, **kwargs):
    from cannula.api import api
    if commit:
        api.keys.write_keys()
        sys.stdout.write("Authorized Keys file updated.\n")
    sys.stdout.write("Dry Run, use --commit to save file.\n\n")
    sys.stdout.write(api.keys.authorized_keys())
    
    

def create_directory(config, key, interactive, logger):
    """Create directory in config, prompt for a new directory if interactive.
    
    Returns an updated config file.
    """
    directory = config.get(key)
    name = key.upper()
    if interactive:
        directory = raw_input("\nCreate %s directory at (%s) \nor enter new path: " % (name, directory)) or directory
    
    if not os.path.isdir(directory):
        logger.info("Creating Directory: %s" % directory)
        os.makedirs(directory, 0700)
    
    config[key] = directory
    return config

def write_file(config, key, template, interactive, logger):
    """
    Write a file to the filesytem, if interactive ask for a new path.
    
    Returns the updated config.
    """
    from cannula.utils import write_file as wf
    f = config.get(key)
    name = key.upper()
    if interactive:
        f = raw_input("\nGenerate %s at (%s) \nor enter new name: " % (name, f)) or f
    
    directory = os.path.dirname(f)
    if not os.path.isdir(directory):
        logger.info("Creating Directory: %s" % directory)
        os.makedirs(directory, 0700)
    
    # Write out the file
    wf(f, template, config)
    
    config[key] = f
    return config

def set_option(config, key, interactive, logger, message=''):
    """Simply set an option, if interactive display message"""
    message = message or "\nSet %s to (%s) \nor enter new option: "
    value = config.get(key)
    name = key.upper()
    if interactive:
        value = raw_input(message % (name, value)) or value
    
    config[key] = value
    return config

def setup_database(config, interactive, logger):
    """Setup the django database."""
    options = [
        'django.db.backends.sqlite3',
        'django.db.backends.mysql',
        'django.db.backends.oracle',
        'django.db.backends.postgresql',
        'django.db.backends.postgresql_psycopg2',
    ]
    selected = config.get('database_engine')
    message = "\nSet %s to (%s) \n"
    message += '\n'.join(['%s [%d] %s' % (('*' if selected == options[i] else ' '), i, options[i]) for i in range(len(options))])
    message += '\nor enter one from the list above:'
    config = set_option(config, 'database_engine', interactive, logger, message)
    
    db = config.get('database_engine')
    try:
        db = options[int(db)]
        config['database_engine'] = db
    except:
        assert(db in options), "Improper Database Backend"
    
    # sqlite3 is special
    if db == 'django.db.backends.sqlite3':
        base = config.get('cannula_base')
        config['database_name'] = os.path.join(base, 'cannula.db')
        config = set_option(config, 'database_name', interactive, logger)
    else:
        config['database_name'] = ''
        config = set_option(config, 'database_name', interactive, logger)
        config = set_option(config, 'database_user', interactive, logger)
        config = set_option(config, 'database_password', interactive, logger)
        config = set_option(config, 'database_host', interactive, logger)
        config = set_option(config, 'database_port', interactive, logger)
    
    return config
    
def initialize(interactive, verbosity):
    levels = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
    logger = logging.getLogger('cannula')
    logger.setLevel(levels.get(int(verbosity)))
    logger.debug("Running Cannula Initialize")
    
    from cannula.conf import conf_dict, write_config
    from cannula.utils import shell
    
    config = conf_dict()
    # save a copy to see if user altered it.
    original = config.copy()
    create_dirs = ['cannula_base']
    for d in create_dirs:
        config = create_directory(config, d, interactive, logger)
    
    # Cannula settings module
    config = set_option(config, 'cannula_settings', interactive, logger,
        message="\nSet %s to (%s) \nor if you are brave you can change this here: ")

    # try to find cannulactl command and prompt user for new setting
    status, cmd = shell('which cannulactl')
    if status == 0:
        config['cannula_cmd'] = cmd.strip()
    config = set_option(config, 'cannula_cmd', interactive, logger)

    # Cannula ssh command, run by authorized keys
    base = config.get('cannula_base')
    ssh_cmd = os.path.join(base, 'bin', 'cannula.sh')
    config['cannula_ssh_cmd'] = ssh_cmd
    config = write_file(config, 'cannula_ssh_cmd', 'cannula/canner.sh', interactive, logger)
    
    # Make sure we have a semi random secret key
    if not config.get('django_secret_key'):
        config['django_secret_key'] = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for _ in range(50)])
    config = set_option(config, 'django_secret_key', interactive, logger)
    
    # Configure the database
    config = setup_database(config, interactive, logger)
    
    # Save the configuration
    if config != original:
        write_config(config)
    
def main():
    parser = OptionParser(__doc__)
    parser.add_option("--settings", dest="settings", help="settings file to use")
    parser.add_option("--noinput", dest="interactive", action='store_false', default=True,
        help="Don't prompt for user input just initialize with defaults.")
    parser.add_option("--verbosity", dest="verbosity", help="Level of output 0-None, 1-Normal, 2-All")
    
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error("incorrect number of arguments")
    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'cannula.settings'
        
    command = args[0]
    
    if command == 'authorized_keys':
        # Write out autorized_keys file
        return keys()
    
    if command == 'initialize':
        return initialize(options.interactive, options.verbosity)
    
    else:
        parser.error("command not found!")

if __name__ == "__main__":
    main()