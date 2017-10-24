import os
import shutil

from django.conf import settings
from subprocess import call


def generate_paddle_docs(original_documentation_dir, output_dir_name):
    # Remove old generated docs directory
    destination_dir = _get_destination_documentation_dir(output_dir_name)
    if os.path.exists(destination_dir) and os.path.isdir(destination_dir):
        shutil.rmtree(destination_dir)

    if os.path.exists(os.path.dirname(original_documentation_dir)):
        destination_dir = _get_destination_documentation_dir(output_dir_name)
        settings_path = settings.PROJECT_ROOT
        script_path = settings_path + '/../../scripts/deploy/generate_paddle_docs.sh'

        if os.path.exists(os.path.dirname(script_path)):
            call([script_path, original_documentation_dir, destination_dir])
            return destination_dir
        else:
            raise Exception('Cannot find script located at %s.' % script_path)
    else:
        raise Exception('Cannot generate documentation, directory %s does not exists.' % original_documentation_dir)


def generate_models_docs(original_documentation_dir, output_dir_name):
    pass


def generate_book_docs(original_documentation_dir, output_dir_name):
    # Remove old generated docs directory
    destination_dir = _get_destination_documentation_dir(output_dir_name)
    if os.path.exists(destination_dir) and os.path.isdir(destination_dir):
        shutil.rmtree(destination_dir)

    if os.path.exists(os.path.dirname(original_documentation_dir)):
        destination_dir = _get_destination_documentation_dir(output_dir_name)
        settings_path = settings.PROJECT_ROOT
        script_path = settings_path + '/../../scripts/deploy/generate_book_docs.sh'

        if os.path.exists(os.path.dirname(script_path)):
            call([script_path, original_documentation_dir, destination_dir])
            return destination_dir
        else:
            raise Exception('Cannot find script located at %s.' % script_path)
    else:
        raise Exception('Cannot generate documentation, directory %s does not exists.' % original_documentation_dir)


def _get_destination_documentation_dir(output_dir_name):
    return '%s/%s' % (settings.GENERATED_DOCS_DIR, output_dir_name)