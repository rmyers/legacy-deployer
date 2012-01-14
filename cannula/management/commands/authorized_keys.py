from django.core.management.base import BaseCommand
from django.conf import settings

# Stop Django from pissing all over the console with debug messages!
settings.DEBUG = False

from cannula.api import api

class Command(BaseCommand):
    help = 'Print out an authorized_keys for the cannula user.'

    def handle(self, *args, **options):
        self.verbosity = 0
        
        base_template = api.keys.authorized_keys()
        
        self.stdout.write(base_template)