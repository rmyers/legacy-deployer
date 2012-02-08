.. Cannula Project documentation master file, created by
   sphinx-quickstart on Sun Feb  5 13:56:27 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Cannula Project's documentation!
===========================================

Cannula is a server that simplifies the creation and deployment of applications
to a single host or a cluster of machines. The goal of this project is to free
up developers from doing sysadmin work. It uses git to handle deployment 
and configuration management. It has a built-in web server (written in django)
but is not required to run, as the deploy process is triggered with a git push::

   $ git push cannula@myhost:mygroup/myproject.git master

Cannula offers a simple way to create a project and groups in order to define
rolls that individuals have. This allows you to limit power on the actual host
systems to those who know what they are doing. With cannula all authentication
is handled with ssh authorized_keys, which defers authorization to the cannula
server. Developers do not need to have ssh access to the machine(s) and/or sudo
permissions. Read security first!

Cannula manages the proxy (nginx or apache) and the individual web applications
it stores all cahnges to configurations in git automatically. This allows you 
to make any change to you stack and simply roll back to a previous setup 
effortlessly. A rollback could either be triggered manually or automatically if 
there was a syntax error which caused an app to not start up.

Cannula is written in Python and much of the built in support centers around
that. However, it should be simple to use other languages as long as you can
start them up with a bash script or write out the correct nginx/apache 
configuration. All the configuration files are just django templates and the
applications can set the context uses to render those templates in the 
:doc:`app.yaml file <configure>`

Contents:

.. toctree::
   :maxdepth: 2
   
   install
   configure
   api



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

