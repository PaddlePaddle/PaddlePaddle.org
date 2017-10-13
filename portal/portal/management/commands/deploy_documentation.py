from django.core.management import BaseCommand
from deploy import documentation

#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "Usage: python manage.py deploy_documentation <source_dir> <version> <output_dir>"

    def add_arguments(self, parser):
        parser.add_argument('source_dir', nargs='+')
        parser.add_argument('version', nargs='+')
        parser.add_argument('output_dir', nargs='+')

    # A command must define handle()
    def handle(self, *args, **options):
        if 'source_dir' in options:
            documentation.transform(
                options['source_dir'][0], options['version'][0], options['output_dir'][0])
