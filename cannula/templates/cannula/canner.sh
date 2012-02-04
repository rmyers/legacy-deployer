#!/bin/bash
#
# This is the main file which preforms all the magic. It should be installed 
# in the home directory of the user that is running cannula (usually cannula).
# Basically when someone ssh's to this user this file is run instead of what ever
# command they were running. This allows us to check permissions first before
# allowing the command to be processed. 
#
# The authorized_keys file looks like this::
#  
#   no-pty,...,command="/path/to/canner johndoe" ssh-rsa JOHNDOE_SSH_PUBLIC_KEY
#   no-pty,...,command="/path/to/canner janedoe" ssh-rsa JANEDOE_SSH_PUBLIC_KEY
#
# This allows us to use ssh to do all the authentication of users with a secure
# public key transaction. All we then need to do is test for the proper
# authorization of each user and the commands they are running.
# 
# This file is written in bash because the cannula scripts could be installed
# anywhere and bash is usually consistent. We just need to tell this script where
# to find the actual files. Also python does not seem to play well with stdin and 
# stdout redirection. (Or maybe I'm to lazy to figure out how to do it properly)
#
# The actual command is stored in the ENV variable 
# $SSH_ORIGINAL_COMMAND, usually "git-receive-pack 'myrepo.git'"
# But it could be some following special commands:
# 
# * info                                - List out all your projects and groups.
# * logs [project]                      - Print out the last few deployment logs.
# * rollback [project] [hash]           - Rollback last deployment, or force 
#                                         'hash' to be deployed.
# * create_group [groupname]            - Create new group.
# * create_project [group] [project]    - Create new project in group.
# * django.syncdb [project]             - Run django syncdb command on project.
#
#

export CANNULA_CMD={{ cannula_cmd }}
export CANNULA_ROOT={{ cannula_base }}

# This needs to be globally available
# This is the settings file of the actual project running cannula
export DJANGO_SETTINGS_MODULE={{ cannula_settings }}

# Check for the user running the command
if [[ ! $1 ]]
then
    echo "Username is required!"
    exit 1
else
    export C_USER=$1
fi

# split 'command args' to see what were running
CMD=`echo $SSH_ORIGINAL_COMMAND | awk '{print $1}'`

# Handle the command
case $CMD in
    "")
        # no command found default just info command
        $CANNULA_CMD $C_USER info
        ;;
        
    "git-receive-pack")
        # Check permissions to repo and strip off any quote chars added by git.
        export REPO=`echo $SSH_ORIGINAL_COMMAND | awk '{print $2}'|sed "s/^\([\"']\)\(.*\)\1\$/\2/g"`
        $CANNULA_CMD $C_USER has_perm read --repo=$REPO
        if [[ ! $? == 0 ]]
        then 
            echo "Access denied!"
            exit 1
        fi
        
        # Initialize the project, this is safe to do 
        # everytime and allows us to pick up any changes to
        # either the base templates or environment settings
        $CANNULA_CMD $C_USER initialize --repo=$REPO
        
        # Do the push and deploy
        $CMD $CANNULA_ROOT/repos/$REPO
        if [[ ! $? == 0 ]]
        then 
            echo "Push failed, please reset project!"
            exit 1
        fi
        
        # Do the actual deployment
        $CANNULA_CMD $C_USER deploy --repo=$REPO
        ;;
        
    *)
        # Just pass everything onto the cannula command
        $CANNULA_CMD $C_USER $SSH_ORIGINAL_COMMAND
        ;;
esac

