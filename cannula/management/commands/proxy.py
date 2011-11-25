from django.core.management.base import BaseCommand

from cannula.conf import proxy

class Command(BaseCommand):
    help = 'Print out a base proxy conf file to use for this project.'

    def handle(self, *args, **options):
        
        base_template = proxy.write_main_conf()
        
        self.stdout.write(base_template)