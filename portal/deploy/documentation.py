import os
import tempfile
import requests
import traceback
from urlparse import urlparse

from django.conf import settings

from deploy import documentation_generator, strip, sitemap_generator
from portal import sitemap_helper
from portal.portal_helper import Content
from portal import portal_helper

def transform(original_documentation_dir, generated_docs_dir, version):
    """
    Given a raw repo directory contents, perform the following steps (conditional to the repo):
    - Generate the output HTML contents from its source content generator engine.
    - Strip their contents from the static files and header, footers, that cause inconsistencies.
    - Generate individual sitemaps.
    """
    try:
        print 'Processing docs at %s to %s for version %s' % (original_documentation_dir, generated_docs_dir, version)
        if not os.path.exists(os.path.dirname(original_documentation_dir)):
            print 'Cannot strip documentation, source_dir=%s does not exists' % original_documentation_dir
            return

        doc_generator = None
        convertor = None
        sm_generator = None
        output_dir_name = None

        if original_documentation_dir:
            original_documentation_dir = original_documentation_dir.rstrip('/')

        dir_path = os.path.dirname(original_documentation_dir)
        path_base_name = os.path.basename(original_documentation_dir)

        # Remove the heading 'v', left in for purely user-facing convenience.
        if version[0] == 'v':
            version = version[1:]

        # If this seems like a request to build/transform the core Paddle docs.
        content_id = portal_helper.FOLDER_MAP_TO_CONTENT_ID.get(path_base_name, None)
        if content_id == Content.DOCUMENTATION:
            doc_generator = documentation_generator.generate_paddle_docs
            convertor = strip.sphinx
            sm_generator = sitemap_generator.sphinx_sitemap

        # Or if this seems like a request to build/transform the book.
        elif content_id == Content.BOOK:
            doc_generator = documentation_generator.generate_book_docs
            convertor = strip.default
            sm_generator = sitemap_generator.book_sitemap

        # Or if this seems like a request to build/transform the models.
        elif content_id == Content.MODELS:
            doc_generator = documentation_generator.generate_models_docs
            convertor = strip.default
            sm_generator = sitemap_generator.models_sitemap

        elif content_id == Content.MOBILE:
            doc_generator = documentation_generator.generate_mobile_docs
            convertor = strip.default
            sm_generator = sitemap_generator.mobile_sitemap

        elif content_id == Content.BLOG:
            doc_generator = documentation_generator.generate_blog_docs

            # move the folder _site/ from generated_docs_dir to content_dir
            convertor = strip.default

            # sm_generator = sitemap_generator.models_sitemap
            sm_generator = None

        else:
            raise Exception('Unsupported content.')

        output_dir_name = content_id

        if not generated_docs_dir:
            # If we have not already generated the documentation, then run the document generator
            print 'Generating documentation at %s' % original_documentation_dir
            if doc_generator:
                generated_docs_dir = doc_generator(original_documentation_dir, output_dir_name)

        print 'Stripping documentation at %s, version %s' % (generated_docs_dir, version)
        if convertor:
            convertor(generated_docs_dir, version, output_dir_name)

        print 'Generating sitemap for documentation at %s, gen_docs_dir=%s,  version %s' % \
              (original_documentation_dir, generated_docs_dir, version)
        if sm_generator:
            sm_generator(original_documentation_dir, generated_docs_dir, version, output_dir_name)

    except Exception as e:
        print 'Unable to process documentation: %s' % e
        traceback.print_exc(original_documentation_dir)


def fetch_and_transform(source_url, version):
    """
    For an arbitrary URL of Markdown contents, fetch and transform them into a
    "stripped" and barebones HTML file.
    """
    response = requests.get(source_url)
    tmp_dir = tempfile.gettempdir()
    source_markdown_file = tmp_dir + urlparse(source_url).path

    if not os.path.exists(os.path.dirname(source_markdown_file)):
        os.makedirs(os.path.dirname(source_markdown_file))

    with open(source_markdown_file, 'wb') as f:
        f.write(response.content)

    strip.markdown_file(source_markdown_file, version, tmp_dir)
