
from setuptools import setup, find_packages

from cannula import version

setup(
    name = 'cannula',
    version = version,
    install_requires = [
        'django >= 1.2.3',
        'virtualenv >= 1.5.1',
    ],
    entry_points = {
        'console_scripts': [
            'cannula-admin = cannula.bin.admin:main',
            'cannulactl = cannula.bin.control:main',
        ]
    },
    url = 'http://bitbucket.org/rmyers/cannula/',
    description = ("A library of tools for deploying Python applications."),
    packages = find_packages(),
    test_suite = 'tests.run_tests',
)