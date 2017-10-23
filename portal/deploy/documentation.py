import os

import zipfile
import tempfile
import requests

from deploy import strip
from deploy import sitemap_generator
from django.conf import settings
from urlparse import urlparse


def transform(source_dir, generated_docs_dir, version):
    if not os.path.exists(os.path.dirname(source_dir)):
        print 'Cannot strip documentation, source_dir=%s does not exists' % source_dir
        return

    convertor = None
    sm_generator = None
    extracted_source_dir = None

    # python manage.py deploy_documentation book v0.10.0 generated_contents/
    # remove the heading 'v'
    if version[0] == 'v':
        version = version[1:]

    if 'documentation' in source_dir.lower():
        convertor = strip.sphinx
        sm_generator = sitemap_generator.sphinx_sitemap

    elif 'book' in source_dir.lower():
        convertor = strip.book
        sm_generator = sitemap_generator.book_sitemap

    elif 'models' in source_dir.lower():
        convertor = strip.models
        sm_generator = sitemap_generator.models_sitemap

    output_dir = '%s/' % (settings.EXTERNAL_TEMPLATE_DIR)
    if convertor:
        if output_dir:
            convertor(extracted_source_dir, version, output_dir)
        else:
            print 'Please provide an output dir or set settings.EXTERNAL_TEMPLATE_DIR'
            return

    if sm_generator:
        if output_dir:
            sm_generator(extracted_source_dir, generated_docs_dir, version, output_dir)
        else:
            print 'Please provide an output dir or set settings.EXTERNAL_TEMPLATE_DIR'
            return


def fetch_and_transform(source_url, version):
    response = requests.get(source_url)
    tmp_dir = tempfile.gettempdir()
    source_markdown_file = tmp_dir + urlparse(source_url).path

    if not os.path.exists(os.path.dirname(source_markdown_file)):
        os.makedirs(os.path.dirname(source_markdown_file))

    with open(source_markdown_file, 'wb') as f:
        f.write(response.content)

    strip.markdown_file(source_markdown_file, version, tmp_dir)
