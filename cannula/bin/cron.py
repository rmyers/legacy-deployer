#!/usr/bin/env python
"""\
%prog [options] cmd

Run cron jobs for cannula.

Available commands:

* authorized_keys: Write out authorized_keys file

"""
import os

from optparse import OptionParser

def keys():
    from cannula.conf import api
    api.keys.write_keys()

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