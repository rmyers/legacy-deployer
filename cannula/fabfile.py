"""
Common utils

"""

from fabric.api import local

def watch_sass():
    local('sass --no-cache --watch static/cannula/scss:static/cannula/css')