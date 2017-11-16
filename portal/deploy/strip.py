import os
from shutil import copyfile, copytree, rmtree
import codecs

from bs4 import BeautifulSoup
import markdown

from django.conf import settings


def sphinx(generated_documentation_dir, version, output_dir_name):
    """
    Strip out the static and extract the body contents, ignoring the TOC,
    headers, and body.
    """
    destination_documentation_dir = _get_destination_documentation_dir(version, output_dir_name)
    if os.path.exists(destination_documentation_dir) and os.path.isdir(destination_documentation_dir):
        rmtree(destination_documentation_dir)

    if generated_documentation_dir:
        generated_documentation_dir = generated_documentation_dir.rstrip('/')

    new_path_map = {
        'develop': {
            '/en/html/': '/en/',
            '/cn/html/': '/zh/',
        },
        '0.10.0': {
            '/en/html/':    '/en/',
            '/cn/html/': '/zh/',
        },
        '0.9.0': {
            '/doc/':    '/en/',
            '/doc_cn/': '/zh/',
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

    print 'strip.sphinx done'

def default(generated_documentation_dir, version, output_dir_name):
    """
    Generates and moves generated output from a source directory to an output
    one, without any transformations or build steps.
    """
    destination_documentation_dir = _get_destination_documentation_dir(version, output_dir_name)

    if os.path.exists(destination_documentation_dir):
        rmtree(destination_documentation_dir)

    copytree(generated_documentation_dir, destination_documentation_dir)


def markdown_file(source_markdown_file, version, tmp_dir):
    """
    Given a markdown file path, generate an HTML partial in a directory nested
    by the path on the URL itself.
    """
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
                    extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables']
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
