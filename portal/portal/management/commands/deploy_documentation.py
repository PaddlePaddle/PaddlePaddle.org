import os
from shutil import copyfile

from django.core.management import BaseCommand

from portal.deploy import transform
from portal import menu_helper, url_helper


# The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = """Usage: python manage.py deploy_documentation
        --content_id=<content_id> --source_dir=<source_dir>
        --destination_dir=<destination_dir> <version>"""

    def add_arguments(self, parser):
        parser.add_argument('--source_dir', dest='source_dir')
        parser.add_argument('--destination_dir', dest='destination_dir')
        parser.add_argument('version', nargs=1)


    def save_menu(self, source_dir, content_id, lang, version):
        # Store a copy of the menu to use when not provided in `develop`.
        menu_path = menu_helper.get_production_menu_path(
            content_id, lang, version)

        menu_dir = os.path.dirname(menu_path)

        if not os.path.exists(menu_dir):
            os.makedirs(menu_dir)

        if content_id == 'api':
            source_dir = os.path.join(source_dir, 'api')

        copyfile(menu_helper._find_menu_in_repo(
            source_dir, 'menu.json'), menu_path)


    # A command must define handle()
    def handle(self, *args, **options):
        # Determine version.
        version = options['version'][0] if 'version' in options else None

        if version[0] == 'v':
            version = version[1:]
        elif version.startswith('release/'):
            version = version[8:]

        # Determine the content_id from the source_dir.
        source_dir = options['source_dir'].rstrip('/')
        content_id = os.path.basename(source_dir).lower()

        menus_to_save = []
        if content_id == 'paddle':
            content_id = 'docs'

            if version in ['0.10.0', '0.11.0']:
                source_dir = os.path.join(source_dir, 'doc')
            else:
                source_dir = os.path.join(source_dir, 'doc', 'fluid')

            menus_to_save.append('api')

        menus_to_save.append(content_id)

        transform(
            source_dir, options.get('destination_dir', None),
            content_id, version, None
        )


        if content_id not in ['models', 'mobile']:
            for lang in ['en', 'zh']:
                for menu_to_save_content_id in menus_to_save:
                    self.save_menu(source_dir, menu_to_save_content_id, lang, version)
