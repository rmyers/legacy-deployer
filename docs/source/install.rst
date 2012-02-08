Installation
============

You should add a new user on you machine for the best results. Log in as
this new user and issue the commands to bootstrap a sample instance of
cannula:

#. Create a cannula user and a virtualenv for the code::

    $ sudo useradd cannula
    $ sudo su - cannula
    $ virtualenv --no-site-packages --distribute --relocatable cannulaenv
    $ source cannulaenv/bin/activate

#. Install cannula::
    
    $ pip install -r https://raw.github.com/rmyers/cannula/master/requirements.txt
     
#. Fire up django dev server::

    $ django-admin.py initialize --settings=cannula.settings
    $ django-admin.py syncdb --settings=cannula.settings
    $ django-admin.py runserver --settings=cannula.settings
    
#. Use the newly spawned server, enjoy!