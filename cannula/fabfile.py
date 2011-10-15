"""
Simple fabric script to simplify setup of new hosts and starting
and stopping workers.


"""
from __future__ import with_statement

import os
import sys
import tarfile
import posixpath
import shutil
import tempfile

from fabric.api import *

from cannula.conf import api, config

# TODO code it!
