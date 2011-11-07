=======================
Example Cannula Project
=======================

You should add a new user on you machine for the best results. Log in as
this new user and issue the commands to bootstrap a sample instance of
cannula:

#. Install cannula::
    
    pip install -r https://raw.github.com/rmyers/cannula/master/requirements.txt
    
#. Run setup in this directory::

    python setup.py develop
     
#. ``cd gitproject``
#. ``python manage.py syncdb``
#. ``python manage.py initialize``
#. ``python manage.py runserver``
#. Use the newly spawned server, enjoy!