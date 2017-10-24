import os
import tempfile
import requests

from deploy import strip
from deploy import sitemap_generator
from django.conf import settings
from urlparse import urlparse


def transform(source_dir, generated_docs_dir, version):
    """
    :param source_dir: raw repo from github
    :param generated_docs_dir: convert markdown to html
    :param version: develop/v0.10.0/v0.9.0
    :return:
    """
    if not os.path.exists(os.path.dirname(source_dir)):
        print 'Cannot strip documentation, source_dir=%s does not exists' % source_dir
        return

    convertor = None
    sm_generator = None
    generated_docs_dir = '%s/' % (settings.WORKSPACE_DIR)

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

    if generated_docs_dir:
        convertor(source_dir, version, generated_docs_dir)
    else:
        print 'Please provide an output dir or set settings.WORKSPACE_DIR'
        return

    if sm_generator:
        if generated_docs_dir:
            sm_generator(source_dir, generated_docs_dir, version, generated_docs_dir)
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
