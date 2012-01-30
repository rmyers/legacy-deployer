#!/bin/bash
#
# Checkout the revision that was just pushed to the remote repo
#
# The "post-receive" script is run after receive-pack has accepted a pack
# and the repository has been updated.  It is passed arguments in through
# stdin in the form
#  <oldrev> <newrev> <refname>
# For example:
#  aa453216d1b3e49e7f6f98441fa56946ddcd6a20 68f7abf4e6f922807889f52bc043ecd31b79f814 refs/heads/master
#

checkout()
{
    newrev=$(git rev-parse $1)
    oldrev=$(git rev-parse $2)
    
    git-checkout -f $newrev &> /dev/null
    
    if [ $? == 0 ]
    then
        echo "Checked out revision $newrev"
        echo "Deploying new version"
        echo "using settings: $DJANGO_SETTINGS_MODULE"
        echo "Repo: $REPO"
        $CANNULA_CMD $C_USER deploy --oldrev=$oldrev --newrev=$newrev --repo=$REPO --settings=$DJANGO_SETTINGS_MODULE
        if [ $? == 0 ]
        then 
            echo "Success!"
        else
            echo "Reverting failed deploy"
            git-checkout -f $oldrev
            # TODO: MAKE A REVERT COMMAND!
            $CANNULA_CMD $C_USER deploy --oldrev=$newrev --newrev=$oldrev --repo=$REPO --settings=$DJANGO_SETTINGS_MODULE
        fi
    else
        echo "Checkout failed, please reset project"
    fi
}

## Main method

if [ -n "$1" -a -n "$2" -a -n "$3" ]; then
        # Output to the terminal in command line mode
        checkout $2
else
        while read oldrev newrev refname
        do
                echo "Preparing to checkout $refname"
                checkout $newrev
        done
fi
