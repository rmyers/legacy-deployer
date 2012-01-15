import datetime

from django.core.management.base import BaseCommand, make_option
from django.conf import settings

settings.DEBUG = False

from cannula.api import api

class Command(BaseCommand):
    help = 'Print out a base proxy conf file to use for this project.'

    option_list = BaseCommand.option_list + (
        make_option('--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Write the file out to the destination.'),
        make_option('--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Display the distination and changes to existing file if any.'),
        make_option('--message', dest='msg', default='%s' % datetime.datetime.now(),
            help='Optional commit message to include.')
        ) 

    def handle(self, *args, **options):
        
        output = api.proxy.write_main_conf(**options)
        
        self.stdout.write(output)
