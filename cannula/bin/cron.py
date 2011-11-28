#!/usr/bin/env python
"""\
%prog [options] cmd

Run cron jobs for cannula.

Available commands:

* authorized_keys: Write out authorized_keys file

"""
import sys
import os
from shutil import copy2

from optparse import OptionParser

def keys():
    from cannula.conf import api
    key_file = api.keys.authorized_keys()
    ssh_path = os.path.expanduser('~/.ssh')
    authorized_keys = os.path.join(ssh_path, 'authorized_keys')
    if not os.path.isdir(ssh_path):
        os.makedirs(ssh_path, mode=0700)
    
    if os.path.isfile(authorized_keys):
        # save the old version just incase
        copy2(authorized_keys, '%s.bak' % authorized_keys)
    
    # Write the authorized keys file
    with open(authorized_keys, 'w') as f:
        f.write(key_file)

def main():
    parser = OptionParser(__doc__)
    parser.add_option("--settings", dest="settings", help="settings file to use")
    
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error("incorrect number of arguments")
    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
        
    command = args[0]
    
    if command == 'authorized_keys':
        # Write out autorized_keys file
        return keys()
    
    else:
        parser.error("command not found!")

if __name__ == "__main__":
    main()