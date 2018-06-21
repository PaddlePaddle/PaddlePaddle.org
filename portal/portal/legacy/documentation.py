import os
import tempfile
import requests
import traceback
from urlparse import urlparse
import json
from subprocess import call
import shutil

from django.conf import settings

from deploy import documentation_generator, strip, sitemap_generator
from deploy.operators import generate_operators_docs_with_generated_doc_dir
from portal import sitemap_helper
from portal.portal_helper import Content
from portal import portal_helper


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

    print 'Generating menu for documentation at %s, gen_docs_dir=%s,  version %s' % \
          (original_documentation_dir, generated_docs_dir, version)
    if sm_generator:
        sm_generator(original_documentation_dir, generated_docs_dir, version, output_dir_name)


# def transformer(original_documentation_dir, generated_docs_dir, version, options=None):
#     """
#     Given a raw repo directory contents, perform the following steps (conditional to the repo):
#     - Generate the output HTML contents from its source content generator engine.
#     - Strip their contents from the static files and header, footers, that cause inconsistencies.
#     - Generate individual sitemaps.
#     """
#     try:
#         print 'Processing docs at %s to %s for version %s' % (original_documentation_dir, generated_docs_dir, version)
#         if not os.path.exists(os.path.dirname(original_documentation_dir)):
#             print 'Cannot strip documentation, source_dir=%s does not exists' % original_documentation_dir
#             return
#
#         if original_documentation_dir:
#             original_documentation_dir = original_documentation_dir.rstrip('/')
#
#         dir_path = os.path.dirname(original_documentation_dir)
#         path_base_name = os.path.basename(original_documentation_dir)
#
#         # Remove the heading 'v', left in for purely user-facing convenience.
#         if version[0] == 'v':
#             version = version[1:]
#
#         # If this seems like a request to build/transform the core Paddle docs.
#         content_id = portal_helper.FOLDER_MAP_TO_CONTENT_ID.get(path_base_name, None)
#         if content_id == Content.DOCUMENTATION:
#             strip.remove_old_dir(version, Content.DOCUMENTATION)
#             strip.remove_old_dir(version, Content.API)
#
#             # Generate Paddle fluid Documentation
#             _execute(original_documentation_dir, generated_docs_dir, version, content_id,
#                      documentation_generator.generate_paddle_docs, strip.sphinx_paddle_fluid,
#                      sitemap_generator.paddle_sphinx_fluid_sitemap, None, options)
#
#             # Generate Paddle v2v1 Documentation
#             _execute(original_documentation_dir, generated_docs_dir, version, content_id,
#                      documentation_generator.generate_paddle_docs, strip.sphinx_paddle_v2v1,
#                      sitemap_generator.paddle_sphinx_v2v1_sitemap, None, options)
#
#             # Process fluid API documentation
#             _execute(original_documentation_dir, generated_docs_dir, version, Content.API,
#                      documentation_generator.generate_paddle_docs, strip.sphinx_paddle_fluid_api,
#                      sitemap_generator.paddle_api_sphinx_fluid_sitemap, None, options)
#
#             # Process V2V1 API documentation
#             _execute(original_documentation_dir, generated_docs_dir, version, Content.API,
#                      documentation_generator.generate_paddle_docs, strip.sphinx_paddle_v2v1_api,
#                      sitemap_generator.paddle_api_sphinx_v2v1_sitemap, None, options)
#
#             # Process paddle mobile documentation
#             _execute(original_documentation_dir, generated_docs_dir, version, 'mobile',
#                      documentation_generator.generate_paddle_docs, strip.sphinx_paddle_mobile_docs,
#                      None, None, options)
#
#         # Or if this seems like a request to build/transform the book.
#         elif content_id == Content.BOOK:
#             _execute(original_documentation_dir, generated_docs_dir, version, content_id,
#                      documentation_generator.generate_book_docs, strip.default,
#                      sitemap_generator.book_sitemap, None, options)
#
#         # Or if this seems like a request to build/transform the models.
#         elif content_id == Content.MODELS:
#             _execute(original_documentation_dir, generated_docs_dir, version, content_id,
#                      documentation_generator.generate_models_docs, strip.default,
#                      sitemap_generator.models_sitemap, None, options)
#
#         elif content_id == Content.MOBILE:
#             _execute(original_documentation_dir, generated_docs_dir, version, content_id,
#                      documentation_generator.generate_mobile_docs, strip.default,
#                      sitemap_generator.mobile_sitemap, None, options)
#
#         elif content_id == Content.BLOG:
#             _execute(original_documentation_dir, generated_docs_dir, version, content_id,
#                      documentation_generator.generate_blog_docs, strip.default,
#                      None, None, options)
#
#         elif content_id == Content.VISUALDL:
#             strip.remove_old_dir(version, content_id)
#
#             _execute(original_documentation_dir, generated_docs_dir, version, content_id,
#                      documentation_generator.generate_visualdl_docs, strip.sphinx,
#                      sitemap_generator.visualdl_sphinx_sitemap, None, options)
#
#         else:
#             raise Exception('Unsupported content.')
#
#     except Exception as e:
#         print 'Unable to process documentation: %s' % e
#         traceback.print_exc(original_documentation_dir)



def sphinx_paddle_fluid(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    new_path_map = {
        'develop': {
            '/fluid/en/html/': '/fluid/en/',
            '/fluid/cn/html/': '/fluid/zh/'
        }
    }
    sphinx(original_documentation_dir, generated_documentation_dir, version, output_dir_name, new_path_map)


def sphinx_paddle_v2v1(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    new_path_map = {
        'develop': {
            '/v2/en/html/': '/en/',
            '/v2/cn/html/': '/zh/'
        },
        '0.10.0': {
            '/en/html/': '/en/',
            '/cn/html/': '/zh/',
        },
        '0.9.0': {
            '/doc/': '/en/',
            '/doc_cn/': '/zh/',
        }
    }
    sphinx(original_documentation_dir, generated_documentation_dir, version, output_dir_name, new_path_map)


def sphinx_paddle_fluid_api(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    new_path_map = {
        'develop': {
            '/fluid/api/en/html/': '/fluid/en/',
            '/fluid/api/cn/html/': '/fluid/zh/'
        }
    }
    sphinx(original_documentation_dir, generated_documentation_dir, version, output_dir_name, new_path_map)


def sphinx_paddle_v2v1_api(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    new_path_map = {
        'develop': {
            '/v2/api/en/html/': '/en/',
            '/v2/api/cn/html/': '/zh/'
        }
    }
    sphinx(original_documentation_dir, generated_documentation_dir, version, output_dir_name, new_path_map)


def sphinx_paddle_mobile_docs(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    new_path_map = {
        'develop': {
            '/mobile/en/html/': '/en/',
            '/mobile/cn/html/': '/zh/'
        }
    }
    sphinx(original_documentation_dir, generated_documentation_dir, version, output_dir_name, new_path_map)


def _get_destination_documentation_dir(version, output_dir_name):
    """
    The destination dir structure looks like below:
    content/blog
    content/docs/<version>/<book|documentation|models>
    """
    if output_dir_name == 'blog':
        return '%s/blog' % settings.EXTERNAL_TEMPLATE_DIR
    return '%s/docs/%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, version, output_dir_name)


def remove_old_dir(version, output_dir_name):
    destination_documentation_dir = _get_destination_documentation_dir(version, output_dir_name)
    if os.path.exists(destination_documentation_dir) and os.path.isdir(destination_documentation_dir):
        rmtree(destination_documentation_dir)


def _find_relative_path(path, subpath_language_dir):
    relative_path = ''
    loc = path.find(subpath_language_dir)
    if loc != -1:
        relative_path = path[loc + len(subpath_language_dir):].strip("/")
    return relative_path


def generate_blog_docs(original_documentation_dir, output_dir_name, options=None):
    # Unlike 'book', 'models' or 'Paddle', for 'blog' we do the strip first then build
    BLOG_TEMPLATE = '<div class="page-content"><div class="wrapper">{{ content }}</div></div>'

    destination_dir = _get_destination_documentation_dir(output_dir_name)
    if os.path.exists(destination_dir) and os.path.isdir(destination_dir):
        shutil.rmtree(destination_dir)

    if os.path.exists(os.path.dirname(original_documentation_dir)):
        destination_dir = _get_destination_documentation_dir(output_dir_name)
        settings_path = settings.PROJECT_ROOT
        script_path = settings_path + '/../../scripts/deploy/generate_blog_docs.sh'

        with open(original_documentation_dir+"/_layouts/default.html", "w") as fp:
            fp.write(BLOG_TEMPLATE)

        if os.path.exists(os.path.dirname(script_path)):
            call([script_path, original_documentation_dir, destination_dir])
            return destination_dir
        else:
            raise Exception('Cannot find script located at %s.' % script_path)
    else:
        raise Exception('Cannot generate documentation, directory %s does not exists.' % original_documentation_dir)


def generate_paddle_docs(original_documentation_dir, output_dir_name, options=None):
    """
    Given a Paddle doc directory, invoke a script to generate docs using Sphinx
    and after parsing the code base based on given config, into an output dir.
    """
    # Remove old generated docs directory
    destination_dir = _get_destination_documentation_dir(output_dir_name)
    if os.path.exists(destination_dir) and os.path.isdir(destination_dir):
        shutil.rmtree(destination_dir)

    if os.path.exists(os.path.dirname(original_documentation_dir)):
        destination_dir = _get_destination_documentation_dir(output_dir_name)
        settings_path = settings.PROJECT_ROOT
        script_path = settings_path + '/../../scripts/deploy/generate_paddle_docs.sh'

        build_type = 'DOC_LITE'
        if options and 'build_type' in options:
            build_type = options['build_type']

        if os.path.exists(os.path.dirname(script_path)):
            call([script_path, original_documentation_dir, destination_dir, build_type])

            return destination_dir
        else:
            raise Exception('Cannot find script located at %s.' % script_path)
    else:
        raise Exception('Cannot generate documentation, directory %s does not exists.' % original_documentation_dir)
