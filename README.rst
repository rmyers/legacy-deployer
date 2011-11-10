
==============
Cannula
==============

This is the basis of the client and server tools written in django to deploy
applications to a production environment. It uses a remote git server to 
handle all deploying. This makes deploying as simple as::
	
	$ git push cannula

Requirements
~~~~~~~~~~~~

* pyyaml
* Django >= 1.3.1
* virtualenv >= 1.5.1
* git
* openssh

Documentation 
~~~~~~~~~~~~~

Developer documentation are located in the 'docs/build/html/' directory. The 
documentation can be built with the command 'make html'. You will need to
have sphinx installed to build the docs. This is still a work in progress.
