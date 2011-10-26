#!/home/rmyers/envs/cannula/bin/python
"""\
%prog [options] username

Test if a user has the correct authorization to do an action.

This is meant to be used in an "authorized_keys" file like this::

    no-pty,...,command="cannula-admin jdoe" ssh-rsa SSH_PUBLIC_KEY

The actual command is stored in the ENV variable 
$SSH_ORIGINAL_COMMAND, usually "git-receive-pack 'myrepo.git'"
But it could be some following special commands:

* info                                - List out all your projects and groups.
* logs [project]                      - Print out the last few deployment logs.
* rollback [project] [hash]           - Rollback last deployment, or force 
                                        'hash' to be deployed.
* create_group [groupname]            - Create new group.
* create_project [group] [project]    - Create new project in group.
* django.syncdb [project]             - Run django syncdb command on project.

Which can be run simply thru ssh like so::

    $ ssh cannula@example.com rollback myproject [commithash]
    $ ssh cannula@example.com create_group newgroup
    $ ssh cannula@example.com create_project newgroup newproject

"""
import sys
import os

from optparse import OptionParser

def info(user):
    from cannula.conf import api
    from django.contrib.auth.models import User
    print os.environ
    print sys.path
    print User.objects.all()
    print api.users.info(user)

def djangoshell(settings):
    # hack sys args
    from django.core.management import execute_from_command_line
    cmd = '/home/rmyers/envs/cannula/bin/django-admin.py'
    args = [cmd, 'shell', '--settings=%s' % settings]
    os.execve(cmd, args, os.environ)

def main():
    parser = OptionParser(__doc__)
    parser.add_option("--settings", dest="settings",
                      help="Django settings file to use")
    
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")
    if not options.settings:
        sys.exit("Cannula users authorized_key file is missing settings file!")
    
    os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
        
    user = args[0]
    command = os.environ.get('SSH_ORIGINAL_COMMAND', 'info')
    
    if command == 'info':
        # Display server and user info
        return info(user)
    
    elif command == 'shell':
        return djangoshell(options.settings)
    
    else:
        parser.error("command not found!")

if __name__ == "__main__":
    main()