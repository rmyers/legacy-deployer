import datetime

from django.core.management.base import BaseCommand, make_option

from cannula.bin.admin import initialize

class Command(BaseCommand):
    help = 'Write out a base supervisor conf file to use.'
    
    option_list = BaseCommand.option_list + (
        make_option('--noinput',
            action='store_false',
            dest='interactive',
            default=True,
            help='Do not prompt user for input just setup the defaults'),
        ) 
    
    def handle(self, *args, **options):
        from django.conf import settings
        settings.LOGGING_CONFIG = None
        return initialize(options.get('interactive'), options.get('verbosity'))