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


def _get_links_in_sections(sections):
    links = []

    for section in sections:
        if 'link' in section:
            for lang, lang_link in section['link'].items():
                links.append('  ' + lang_link)

        if 'sections' in section:
            links += _get_links_in_sections(section['sections'])

    return links


def _build_sphinx_index_from_sitemap(sitemap_path, lang):
    links = ['..  toctree::', '  :maxdepth: 1', '']

    # Generate an index.rst based on the sitemap.
    with open(sitemap_path, 'r') as sitemap_file:
        sitemap = json.loads(sitemap_file.read())
        links += _get_links_in_sections(sitemap['sections'])

    # Manual hack because the documentation marks the language code differently.
    if lang == 'zh':
        lang = 'cn'

    with open(os.path.dirname(sitemap_path) + ('/index_%s.rst' % lang), 'w') as index_file:
        index_file.write('\n'.join(links))


def _remove_sphinx_menu(menu_path, lang):
    """Undoes the function above"""
    os.remove(os.path.dirname(menu_path) + ('/index_%s.rst' % lang))


def transform(content_id, lang, source_dir, destination_dir):
    # try:
    print 'Processing docs at %s to %s' % (source_dir, destination_dir)

    menu_path = source_dir + '/menu.json'

    # Regenerate its contents.
    if content_id in ['documentation', 'api']:
        _build_sphinx_index_from_sitemap(menu_path, lang)

        sphinx_output_dir = '/Users/aroravarun/Code/paddlepaddle/scratch/sp' # tempfile.mkdtemp()

        call(['sphinx-build', '-b', 'html', '-c',
            os.path.join(settings.SPHINX_CONFIG_DIR, lang), source_dir, sphinx_output_dir])

        strip.sphinx(source_dir, sphinx_output_dir, destination_dir)

        _remove_sphinx_menu(menu_path, lang)

        #shutil.rmtree(sphinx_output_dir)

    elif content_id == 'book':
        documentation_generator.generate_book_docs(source_dir, destination_dir)

    elif content_id == 'models':
        documentation_generator.generate_models_docs(
            source_dir, destination_dir)


    # except Exception as e:
    #     print 'Unable to process documentation: %s' % e
    #     traceback.print_exc(original_documentation_dir)







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
