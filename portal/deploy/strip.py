import os
from shutil import copyfile, copytree, rmtree
import codecs

from bs4 import BeautifulSoup
import markdown

from django.conf import settings

# Traverse through all the dirs of a given path.
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# generated_documentation_dir = BASE_DIR + '/docs'
# destination_documentation_dir = BASE_DIR + '/documentation'

# Using the map for a new directory mapping, determine a new location for the transformed file.


def sphinx(generated_documentation_dir, version, output_dir_name):
    """
    Strip out the static and extract the body contents, ignoring the TOC,
    headers, and body.
    """
    destination_documentation_dir = _get_destination_documentation_dir(version, output_dir_name)
    if os.path.exists(destination_documentation_dir) and os.path.isdir(destination_documentation_dir):
        rmtree(destination_documentation_dir)


    new_path_map = {
        'develop': {
            '/en/html/': '/en/',
            '/cn/html/': '/cn/',
        },
        '0.10.0': {
            '/doc/':    '/doc/',
            '/doc_cn/': '/doc_cn/',
        },
        '0.9.0': {
            '/doc/':    '/doc/',
            '/doc_cn/': '/doc_cn/',
        }
    }

    # if the version is not supported, fall back to 'develop'
    if version not in new_path_map:
        version = 'develop'

    # Go through each file, and if it is a .html, extract the .document object
    #   contents
    for subdir, dirs, all_files in os.walk(generated_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                generated_documentation_dir):]
            subpath_language_dir = None
            if version in new_path_map:
                new_path_map_prefixes = new_path_map[version].keys()
                subpath_language_dirs = [new_path_map_prefixes[0], new_path_map_prefixes[1]]

                if subpath.startswith(subpath_language_dirs[0]):
                    subpath_language_dir = subpath_language_dirs[0]
                elif subpath.startswith(subpath_language_dirs[1]):
                    subpath_language_dir = subpath_language_dirs[1]

                if subpath_language_dir:
                    new_path = destination_documentation_dir + (
                        new_path_map[version][subpath_language_dir]
                        + subpath[len(subpath_language_dir):])

                    if '.html' in file or '_images' in subpath or '.txt' in file:
                        if not os.path.exists(os.path.dirname(new_path)):
                            os.makedirs(os.path.dirname(new_path))

                    if '.html' in file:
                        # Soup the body of the HTML file.
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
                    elif '_images' in subpath or '.txt' in file:
                        # Copy to images directory.
                        copyfile(os.path.join(subdir, file), new_path)
                    elif 'searchindex.js' in subpath:
                        copyfile(os.path.join(subdir, file), new_path)


def book(generated_documentation_dir, version, output_dir_name):
    """
    Strip out the static and extract the body contents, ignoring the TOC,
    headers, and body.
    """
    # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
    # and transform them using a markdown library.
    destination_documentation_dir = _get_destination_documentation_dir(version, output_dir_name)

    for subdir, dirs, all_files in os.walk(generated_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                generated_documentation_dir):]
            new_path = '%s/%s' % (destination_documentation_dir, subpath)

            if '.html' in file or 'image/' in subpath:
                if not os.path.exists(os.path.dirname(new_path)):
                    os.makedirs(os.path.dirname(new_path))

            if '.html' in file:
                # Soup the body of the HTML file.
                with open(os.path.join(subdir, file)) as original_html_file:
                    soup = BeautifulSoup(original_html_file, 'html.parser')

                # Find the markdown element.
                markdown_body = soup.select('div#markdown')

                # NOTE: This ignores the root index files.
                if len(markdown_body) > 0:
                    with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                        # Strip out the wrapping HTML
                        new_html_partial.write(
                            '{% verbatim %}\n' + markdown.markdown(
                                '\n'.join(unicode(str(markdown_body[0]), 'utf-8').split('\n')[1:-2]),
                                extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables']
                            ) + '\n{% endverbatim %}'
                        )

            elif 'image/' in subpath:
                copyfile(os.path.join(subdir, file), new_path)


def models(generated_documentation_dir, version, output_dir_name):
    destination_documentation_dir = _get_destination_documentation_dir(version, output_dir_name)

    if os.path.exists(destination_documentation_dir):
        rmtree(destination_documentation_dir)
    copytree(generated_documentation_dir, destination_documentation_dir)


def markdown_file(source_markdown_file, version, tmp_dir):
    new_path = '%s/docs/%s/other/%s' % (
        settings.EXTERNAL_TEMPLATE_DIR, version, os.path.splitext(
        source_markdown_file.replace(tmp_dir, ''))[0] + '.html')

    if not os.path.exists(os.path.dirname(new_path)):
        os.makedirs(os.path.dirname(new_path))

    with open(source_markdown_file) as original_md_file:
        markdown_body = original_md_file.read()

        with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
            # Strip out the wrapping HTML
            new_html_partial.write(
                '{% verbatim %}\n' + markdown.markdown(
                    unicode(markdown_body, 'utf-8'),
                    extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables']
                ) + '\n{% endverbatim %}'
            )


def _get_destination_documentation_dir(version, output_dir_name):
    return '%s/docs/%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, version, output_dir_name)
