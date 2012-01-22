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

from optparse import OptionParser

def info(user):
    from cannula.api import api
    print api.users.info(user)

def create_group(user, name, description):
    from cannula.api import api
    return api.groups.create(name, user, description)

def initialize(user, repo):
    """Initialize the git repo for this project."""
    if '/' not in repo:
        sys.exit("Invalid repo: %s" % repo)
    _, project = repo.split('/')
    if '.' not in project:
        sys.exit("Invalid repo: %s" % repo)
    project, _ = project.split('.')
    
    from cannula.api import api
    try:
        api.projects.initialize(project, user)
    except Exception, e:
        sys.exit("Error initializing project: %s" % e)
    return True

def deploy(user, repo):
    return True

def has_perm(user, perm, group=None, project=None, repo=None):
    """
    Check that a user has a certain permission. 
    Exit non-zero if not so bash scripts may use this.
    """
    from cannula.api import api
    if repo is not None:
        # TODO: make this better
        group = repo.split('/')[0]
    if api.permissions.has_perm(user, perm, project=project, group=group):
        return True
    sys.exit("Access Denied!")

def main():
    parser = OptionParser(__doc__)
    parser.add_option("--settings", dest="settings", help="settings file to use")
    parser.add_option("--project", dest="project", help="project to update")
    parser.add_option("--group", dest="group",help="group to update")
    parser.add_option("--repo", dest="repo", help="repo to update")
    
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error("incorrect number of arguments")
    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'cannula.settings'
        
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
        return initialize(user=user, repo=options.repo)
    
    elif command == 'deploy':
        return deploy(user=user, repo=options.repo)
    
    elif command == 'has_perm':
        # user has_perm perm --project=project --group=group
        if len(args) > 3:
            parser.error("Must specify permission!")
        perm = args[2]
        return has_perm(user, perm, group=options.group, 
            project=options.project, repo=options.repo)
    
    else:
        parser.error("command not found!")

if __name__ == "__main__":
    main()