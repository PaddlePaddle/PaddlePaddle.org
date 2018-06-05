import os
import re
from shutil import copyfile, copytree, rmtree
import codecs

from bs4 import BeautifulSoup
import markdown

from django.conf import settings
from deploy.utils import MARKDOWN_EXTENSIONS


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


def sphinx(original_documentation_dir, generated_documentation_dir, destination_documentation_dir, version=None, output_dir_name=None, new_path_map=None):
    """
    Strip out the static and extract the body contents, ignoring the TOC,
    headers, and body.
    """
    # destination_documentation_dir = _get_destination_documentation_dir(version, output_dir_name)
    # if generated_documentation_dir:
    #     generated_documentation_dir = generated_documentation_dir.rstrip('/')
    #
    # if not new_path_map:
    #     new_path_map = {
    #         'develop': {
    #             '/fluid/en/html/': '/fluid/en/',
    #             '/fluid/cn/html/': '/fluid/zh/'
    #         }
    #     }
    #         '0.10.0': {
    #             '/en/html/':    '/en/',
    #             '/cn/html/': '/zh/',
    #         },
    #         '0.9.0': {
    #             '/doc/':    '/en/',
    #             '/doc_cn/': '/zh/',
    #         }
    #     }

    # if the version is not supported, fall back to 'develop'
    # if version not in new_path_map:
    # version = 'develop'

    # Go through each file, and if it is a .html, extract the .document object
    #   contents
    for subdir, dirs, all_files in os.walk(generated_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                generated_documentation_dir):]
            # if version in new_path_map:
                # subpath_language_dirs = new_path_map[version].keys()

                # for subpath_language_dir in subpath_language_dirs:
                    # Check if the we should process the file or not
                    # if subpath_language_dir and subpath.startswith(subpath_language_dir):

            if not subpath.startswith('/.') and not subpath.startswith(
                '/_static') and not subpath.startswith('/_doctrees'):
                # new_path = destination_documentation_dir + (
                #     new_path_map[version][subpath_language_dir]
                #     + subpath[len(subpath_language_dir):])
                new_path = destination_documentation_dir + subpath

                if '.html' in file or '_images' in subpath or '.txt' in file or '.json' in file:
                    if not os.path.exists(os.path.dirname(new_path)):
                        os.makedirs(os.path.dirname(new_path))

                if '.html' in file:
                    # Soup the body of the HTML file.
                    # Check if this HTML was generated from Markdown
                    # original_md_path = get_original_markdown_path(original_documentation_dir,
                    #                                               subdir, subpath_language_dir, file)

                    original_md_path = get_original_markdown_path(
                        original_documentation_dir, subpath[1:])

                    if original_md_path:
                        # If this html file was generated from Sphinx MD, we need to regenerate it using python's
                        # MD library.  Sphinx MD library is limited and doesn't support tables
                        markdown_file(original_md_path, version, '', new_path)

                        # Since we are ignoring SPHINX's generated HTML for MD files (and generating HTML using
                        # python's MD library), we must fix any image links that starts with 'src/'.
                        image_subpath = None

                        #relative_path = _find_relative_path(subdir, subpath_language_dir)
                        #if relative_path:
                        # figure out the relative path of the file to the root, and append a ../ on each parent
                        parent_paths = subpath.split('/')
                        image_subpath = ''
                        for i in range(len(parent_paths)):
                            image_subpath = image_subpath + '../'
                        image_subpath += '_images'  # hardcode the sphinx '_images' dir

                        with open(new_path) as original_html_file:
                            soup = BeautifulSoup(original_html_file, 'lxml')

                            image_links = soup.find_all('img', src=re.compile(r'^(?!http).*'))

                            if len(image_links) > 0:
                                for image_link in image_links:
                                    image_file_name = os.path.basename(image_link['src'])

                                    if image_subpath:
                                        image_link['src'] = '%s/%s' % (image_subpath, image_file_name)
                                    else:
                                        image_link['src'] = '_images/%s' % (image_file_name)

                                with open(new_path, 'w') as new_html_partial:
                                    new_html_partial.write(soup.encode("utf-8"))
                    else:
                        with open(os.path.join(subdir, file)) as original_html_file:
                            soup = BeautifulSoup(original_html_file, 'lxml')

                        document = None
                        # Find the .document element.
                        if version == '0.9.0':
                            document = soup.select('div.body')[0]
                        else:
                            document = soup.select('div.document')[0]
                        with open(new_path, 'w') as new_html_partial:
                            new_html_partial.write(document.encode("utf-8"))
                elif '_images' in subpath or '.txt' in file or '.json' in file:
                    # Copy to images directory.
                    copyfile(os.path.join(subdir, file), new_path)
                elif 'searchindex.js' in subpath:
                    copyfile(os.path.join(subdir, file), new_path)

    print 'strip.sphinx done'


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


def get_original_markdown_path(original_documentation_dir, file):
    """
    Finds the path of the original MD file that generated the html file located at "path"
    :param original_documentation_dir:
    :param path:
    :param subpath_language_dir:
    :param file:
    :return:
    """
    # relative_path = _find_relative_path(path, subpath_language_dir)
    filename, _ = os.path.splitext(file)
    # original_file_path = '%s/doc/%s/%s.md' % (original_documentation_dir, relative_path, filename)
    original_file_path = '%s/%s.md' % (original_documentation_dir, filename)

    if os.path.isfile(original_file_path):
        return original_file_path
    else:
        return None


def default(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    """
    Generates and moves generated output from a source directory to an output
    one, without any transformations or build steps.
    """
    destination_documentation_dir = _get_destination_documentation_dir(version, output_dir_name)

    if os.path.exists(destination_documentation_dir):
        rmtree(destination_documentation_dir)

    copytree(generated_documentation_dir, destination_documentation_dir)


def markdown_file(source_markdown_file, version, tmp_dir, new_path=None):
    """
    Given a markdown file path, generate an HTML partial in a directory nested
    by the path on the URL itself.
    """
    if not new_path:
        new_path = settings.OTHER_PAGE_PATH % (
            settings.EXTERNAL_TEMPLATE_DIR, version, os.path.splitext(
            source_markdown_file.replace(tmp_dir, ''))[0] + '.html')

    # Create the nested directories if they don't exist.
    if not os.path.exists(os.path.dirname(new_path)):
        os.makedirs(os.path.dirname(new_path))

    with open(source_markdown_file) as original_md_file:
        markdown_body = original_md_file.read()

        with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
            # Strip out the wrapping HTML
            new_html_partial.write(
                '{% verbatim %}\n' + markdown.markdown(
                    unicode(markdown_body, 'utf-8'),
                    extensions=MARKDOWN_EXTENSIONS
                ) + '\n{% endverbatim %}'
            )


def _get_destination_documentation_dir(version, output_dir_name):
    """
    The destination dir structure looks like below:
    content/blog
    content/docs/<version>/<book|documentation|models>
    """
    if output_dir_name == 'blog':
        return '%s/blog' % settings.EXTERNAL_TEMPLATE_DIR
    return '%s/docs/%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, version, output_dir_name)
