import os
import tempfile
import requests
import traceback
from urlparse import urlparse

from django.conf import settings

from deploy import documentation_generator, strip, sitemap_generator
from deploy.operators import generate_operators_docs_with_generated_doc_dir
from portal import sitemap_helper
from portal.portal_helper import Content
from portal import portal_helper

def transform(original_documentation_dir, generated_docs_dir, version, options=None):
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
            # Generate Paddle Documentation
            _execute(original_documentation_dir, generated_docs_dir, version, content_id,
                     documentation_generator.generate_paddle_docs, strip.sphinx,
                     sitemap_generator.paddle_sphinx_sitemap, None, options)

            # Generate Paddle API Documentation
            output_dir_name = Content.API
            if generated_docs_dir:
                # Since Paddle API documents exists as a subdirectory 'api' within paddle docs, we append 'api' to it
                generated_docs_dir = '%s/%s' % (generated_docs_dir, output_dir_name)

            # TODO(thuan): Fix document generator for API documentation.  For now, we are only going to support
            #   stripping/generating sitemaps for pre generated Paddle documentation
            _execute(original_documentation_dir, generated_docs_dir, version, 'api',
                     documentation_generator.generate_paddle_docs, strip.sphinx,
                     sitemap_generator.paddle_api_sphinx_sitemap, None, options)

        # Or if this seems like a request to build/transform the book.
        elif content_id == Content.BOOK:
            _execute(original_documentation_dir, generated_docs_dir, version, content_id,
                     documentation_generator.generate_book_docs, strip.default,
                     sitemap_generator.book_sitemap, None, options)

        # Or if this seems like a request to build/transform the models.
        elif content_id == Content.MODELS:
            _execute(original_documentation_dir, generated_docs_dir, version, content_id,
                     documentation_generator.generate_models_docs, strip.default,
                     sitemap_generator.models_sitemap, None, options)

        elif content_id == Content.MOBILE:
            _execute(original_documentation_dir, generated_docs_dir, version, content_id,
                     documentation_generator.generate_mobile_docs, strip.default,
                     sitemap_generator.mobile_sitemap, None, options)

        elif content_id == Content.BLOG:
            _execute(original_documentation_dir, generated_docs_dir, version, content_id,
                     documentation_generator.generate_blog_docs, strip.default,
                     None, None, options)

        elif content_id == Content.VISUALDL:
            _execute(original_documentation_dir, generated_docs_dir, version, content_id,
                     documentation_generator.generate_visualdl_docs, strip.sphinx,
                     sitemap_generator.visualdl_sphinx_sitemap, None, options)

        else:
            raise Exception('Unsupported content.')

    except Exception as e:
        print 'Unable to process documentation: %s' % e
        traceback.print_exc(original_documentation_dir)


def _execute(original_documentation_dir, generated_docs_dir, version, output_dir_name, doc_generator,
             convertor, sm_generator, post_generator, options=None):
    if not generated_docs_dir:
        # If we have not already generated the documentation, then run the document generator
        print 'Generating documentation at %s' % original_documentation_dir
        if doc_generator:
            generated_docs_dir = doc_generator(original_documentation_dir, output_dir_name, options)

    if post_generator:
        # Run any post generator steps
        post_generator(generated_docs_dir, output_dir_name)

    print 'Stripping documentation at %s, version %s' % (generated_docs_dir, version)
    if convertor:
        convertor(original_documentation_dir, generated_docs_dir, version, output_dir_name)

    print 'Generating sitemap for documentation at %s, gen_docs_dir=%s,  version %s' % \
          (original_documentation_dir, generated_docs_dir, version)
    if sm_generator:
        sm_generator(original_documentation_dir, generated_docs_dir, version, output_dir_name)


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
