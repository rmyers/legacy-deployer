from django.core.management.base import BaseCommand, make_option
from django.conf import settings

# Stop Django from pissing all over the console with debug messages!
settings.DEBUG = False

from cannula.api import api

class Command(BaseCommand):
    help = 'Print out an authorized_keys for the cannula user.'
    
    option_list = BaseCommand.option_list + (
        make_option('--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Write the authorized_keys file to ~/.ssh directory.'),
        )
    
    def handle(self, *args, **options):
        if options.get('commit'):
            api.keys.write_keys()
        else:
            self.stdout.write("dry-run\n")
            self.stdout.write(api.keys.authorized_keys())