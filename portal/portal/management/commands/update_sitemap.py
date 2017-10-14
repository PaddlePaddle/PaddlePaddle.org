from django.core.management import BaseCommand
from portal import sitemap_helper

#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "Usage: python manage.py update_sitemap <version>"

    def add_arguments(self, parser):
        parser.add_argument('version', nargs='+')

    # A command must define handle()
    def handle(self, *args, **options):
        if 'version' in options:
            for version in options['version']:
                sitemap_helper.generate_sitemap(version)