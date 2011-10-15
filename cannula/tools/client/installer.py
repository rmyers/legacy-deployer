"""
Installer
=========

This is a Jython module which creates a cross platform GUI installer 
that doesn't even require that Python is installed. This is also 
meant to be used from a Java Web Start jar file. 

To Package a new installer tool simply edit this file and run ant.

Test it out by installing Jython and run this file::

    $ jython installer.py

"""

import javax.swing as swing