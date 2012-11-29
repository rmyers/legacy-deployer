from django.core.management.base import BaseCommand, make_option
from django.conf import settings

# Stop Django from pissing all over the console with debug messages!
settings.DEBUG = False

from cannula.bin.admin import keys

class Command(BaseCommand):
    help = 'Print out an authorized_keys for the cannula user.'
    
    option_list = BaseCommand.option_list + (
        make_option('--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Write the authorized_keys file to ~/.ssh directory.')
        )
    
    def handle(self, *args, **options):
        output = keys(*args, **options)
        self.stdout.write(output)