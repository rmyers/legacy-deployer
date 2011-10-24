from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

from cannula import version

setup(
    name = 'cannula',
    version = version,
    install_requires = [
        'django >= 1.3.1',
        #'fabric >= 1.0.0',
        'virtualenv >= 1.4.5',
        'celery',
        'django-kombu',
        'django-celery',
        'jinja2',
    ],
    url = 'http://bitbucket.org/rmyers/cannula/',
    description = ("A library of tools for deploying Python applications."),
    packages = find_packages(),
    test_suite = 'tests.run_tests',
)