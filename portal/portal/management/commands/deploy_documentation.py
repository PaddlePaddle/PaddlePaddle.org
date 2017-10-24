from django.core.management import BaseCommand
from deploy import documentation

#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "Usage: python manage.py deploy_documentation --source=<source> --dest_gen_docs_dir=<dest_gen_docs_dir> --version=<version> --post_gen_docs_dir=<post_gen_docs_dir>"

    def add_arguments(self, parser):
        parser.add_argument('--source', dest='source')
        parser.add_argument('--dest_gen_docs_dir', dest='dest_gen_docs_dir')
        parser.add_argument('--doc_version', dest='doc_version')

    # A command must define handle()
    def handle(self, *args, **options):
        documentation.transform(
            options['source'],
            options.get('dest_gen_docs_dir', None),
            options['doc_version'])
