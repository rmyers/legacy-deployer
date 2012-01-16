import datetime

from django.core.management.base import BaseCommand, make_option

from cannula.api import api

class Command(BaseCommand):
    help = 'Write out a base supervisor conf file to use.'
    
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
        
        base_template = api.proc.write_main_conf(**options)
        
        self.stdout.write(base_template)