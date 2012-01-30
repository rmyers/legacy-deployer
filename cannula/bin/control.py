#!/usr/bin/env python
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
import re

from optparse import OptionParser

NAME_MATCH = re.compile('^([a-zA-Z][-_a-zA-Z0-9]*)/([a-zA-Z][-_a-zA-Z0-9]*)\.git')

def info(user):
    from cannula.api import api
    print api.users.info(user)

def create_group(user, name, description):
    from cannula.api import api
    return api.groups.create(name, user, description)

def initialize(user, project):
    """Initialize the git repo for this project."""
    from cannula.api import api
    try:
        api.projects.initialize(project, user)
    except Exception, e:
        sys.exit("Error initializing project: %s" % e)
    sys.exit(0)

def deploy(user, project, oldrev, newrev):
    from cannula.api import api
    try:
        api.deploy.deploy(project, user, oldrev, newrev)
    except Exception, e:
        raise
        sys.exit("Error deploying project: %s" % e)
    sys.exit(0)

def has_perm(user, perm, group=None, project=None):
    """
    Check that a user has a certain permission. 
    Exit non-zero if not so bash scripts may use this.
    """
    from cannula.api import api
    if api.permissions.has_perm(user, perm, group=group, project=project):
        return True
    sys.exit("Access Denied!")

def main():
    parser = OptionParser(__doc__)
    parser.add_option("--settings", dest="settings", help="settings file to use")
    parser.add_option("--project", dest="project", help="project to update")
    parser.add_option("--group", dest="group",help="group to update")
    parser.add_option("--repo", dest="repo", help="repo to update")
    parser.add_option("--oldrev", dest="oldrev", help="Previous revision of repository")
    parser.add_option("--newrev", dest="newrev", help="New revision of repository")
    
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error("incorrect number of arguments")
    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'cannula.settings'
    
    # Parse the group and project from repo or group/project options
    group = None
    project = None
    if options.repo:
        match = NAME_MATCH.match(options.repo)
        if not match:
            parser.error("Invalid Repository")
        group = match.group(1)
        project = match.group(2)
    if options.project:
        project = options.project
    if options.group:
        group = options.group
        
    user = args[0]
    command = args[1]
    
    if command == 'info':
        # Display server and user info
        return info(user)
    
    elif command == 'log':
        # user log message --project=project --group=group
        if len(args) > 3:
            parser.error("Must specify log message!")
    
    elif command == 'create_group':
        # user create_group groupname description
        if len(args) > 3:
            parser.error("Must specify group name!")
        groupname = args[2]
        description = ""
        if len(args) > 4:
            description = args[3]
        return create_group(user, groupname, description)
    
    elif command == 'initialize':
        return initialize(user=user, project=project)
    
    elif command == 'deploy':
        return deploy(user=user, project=project, oldrev=options.oldrev, 
            newrev=options.newrev)
    
    elif command == 'has_perm':
        # user has_perm perm --project=project --group=group
        if len(args) > 3:
            parser.error("Must specify permission!")
        perm = args[2]
        return has_perm(user, perm, group=group, project=project)
    
    else:
        parser.error("command not found!")

if __name__ == "__main__":
    main()