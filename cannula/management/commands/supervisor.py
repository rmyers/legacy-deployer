from django.core.management.base import BaseCommand

from cannula.conf import supervisor

class Command(BaseCommand):
    help = 'Print out a base proxy conf file to use for this project.'

    def handle(self, *args, **options):
        
        base_template = supervisor.write_main_conf()
        
        self.stdout.write(base_template)