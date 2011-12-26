
from setuptools import setup, find_packages

from cannula import version

setup(
    name = 'gitproject',
    version = version,
    install_requires = [
        'flask',
        'passlib',
        'jinja2',
        'cannula >= 0.1.0-a',
    ],
    url = 'http://github.com/rmyers/cannula/',
    description = ("Sample project for deploying a cannula site."),
    packages = find_packages()
)