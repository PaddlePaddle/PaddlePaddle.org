from deploy import strip
from django.conf import settings
import requests
import zipfile


def transform(source_dir, version, output_dir):
    convertor = None
    extracted_source_dir = None

    if source_dir in settings.GIT_REPO_MAP:
        git_repo = settings.GIT_REPO_MAP[source_dir]
        git_repo = git_repo + version + '.zip'
        if version[0] == 'v':
            version = version[1:]
        extracted_dir = source_dir + '-' + version
        response = requests.get(git_repo)
        tmp_zip_file = settings.TEMPORARY_DIR + source_dir + '.zip'

        with open(tmp_zip_file, 'wb') as f:
            f.write(response.content)

        with zipfile.ZipFile(tmp_zip_file, "r") as zip_ref:
            zip_ref.extractall(settings.TEMPORARY_DIR)
            extracted_source_dir = settings.TEMPORARY_DIR + '/' + extracted_dir

    if 'documentation' in source_dir:
        convertor = strip.sphinx

    elif 'book' in source_dir:
        convertor = strip.book

    elif 'models' in source_dir:
        convertor = strip.models

    if convertor:
        # convertor(extracted_source_dir, version, settings.EXTERNAL_TEMPLATE_DIR)
        convertor(extracted_source_dir, version, output_dir)
