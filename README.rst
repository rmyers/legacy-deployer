
==============
Cannula
==============

This is the basis of the client and server tools written in django to deploy
applications to a production environment. It uses a remote git server to 
handle all deploying. This makes deploying as simple as::
	
	$ git push cannula master

Requirements
~~~~~~~~~~~~

* pyyaml
* Django >= 1.3.1
* virtualenv >= 1.5.1
* supervisor
* git
* openssh

Documentation 
~~~~~~~~~~~~~

Developer documentation are located in the 'docs/build/html/' directory. The 
documentation can be built with the command 'make html'. You will need to
have sphinx installed to build the docs. This is still a work in progress.

Quick Install
~~~~~~~~~~~~~

You should add a new user on you machine for the best results. Log in as
this new user and issue the commands to bootstrap a sample instance of
cannula:

#. Install the dependancies (ubuntu)::

	$ sudo apt-get install python-dev build-essential nginx python-pip \
	  python-virtualenv git

#. Create a cannula user and a virtualenv for the code::

    $ sudo adduser cannula --disabled-password --home /cannula
    $ sudo su - cannula
    $ virtualenv cannulaenv
    $ source cannulaenv/bin/activate

#. Install cannula::
    
    pip install -r https://raw.github.com/rmyers/cannula/master/requirements.txt
     
#. Fire up django dev server::

    django-admin.py initialize --settings=cannula.settings
    django-admin.py syncdb --settings=cannula.settings
    django-admin.py runserver --settings=cannula.settings
    
#. Use the newly spawned server, enjoy!

Security
~~~~~~~~

Security is good, this is one of the advantanges of using cannula. You can give
a developer access to just deploy a single application or server without giving
them ssh access and sudo. You should also secure the machine to disable 
password authentication (once you have your ssh keys setup of course)

Edit your ``/etc/ssh/sshd_config``::

	PasswordAuthentication no

Then restart sshd. Now on the plus side you wont get thousands of login attempts
by bots using a dictionary brute force.

Configuration
~~~~~~~~~~~~~

All configuration settings for cannula are stored in a conf file 'ini' style.
by default cannula will look in /etc/cannula/cannula.conf and ~/.cannula.conf
you can have a look at the defaults here: 

https://raw.github.com/rmyers/cannula/master/cannula/defaults.cfg

Deploying An Application
~~~~~~~~~~~~~~~~~~~~~~~~

Application just need to specify an app.yaml file to tell cannula how to deploy
it. Currently the only handler that is available is gunicorn_django, but it 
should be easy to add any others. Here is a sample app.yaml file::

    # optional domain to listen on
    domain: example.com
    # optional version string
    version: 1.0
    # runtime (ruby, python, php, java)
    runtime: python
    api_version: 1
    
    # setup some defaults to pass to handlers
    gunicorn_defaults: 
      workers: 2
      worker-class: sync
      worker-connections: 1000
      max_requests: 0
      timeout: 30
      keepalive: 2
      
    # Main wsgi handlers and static file definitions
    # Each unique 'worker' handler will setup a separate process
    handlers:
    # static files (less greedy urls should come first!)
    - url: /static
      static_dir: static
    
    # special handler for backend this will spawn a separate gunicorn process
    - url: /backend/
      worker: cannula.worker.gunicorn_django
      settings: backend_settings
      defaults: gunicorn_defaults
    
    # Main site handler will match everything else
    - url: /
      worker: cannula.worker.gunicorn_django
      settings: main_settings
      defaults: gunicorn_defaults
