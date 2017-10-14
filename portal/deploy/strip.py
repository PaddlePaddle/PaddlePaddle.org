import os
from shutil import copyfile
import codecs

from bs4 import BeautifulSoup
import markdown

# Traverse through all the dirs of a given path.
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# original_documentation_dir = BASE_DIR + '/docs'
# destination_documentation_dir = BASE_DIR + '/documentation'

# Using the map for a new directory mapping, determine a new location for the transformed file.


def sphinx(original_documentation_dir, version, destination_documentation_dir):
    """
    Strip out the static and extract the body contents, ignoring the TOC,
    headers, and body.
    """
    new_path_map = {
        '/en/html/': '/%s/en/' % version,
        '/cn/html/': '/%s/cn/' % version
    }

    # Go through each file, and if it is a .html, extract the .document object
    #   contents
    for subdir, dirs, all_files in os.walk(original_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                original_documentation_dir):]
            subpath_language_dir = subpath[:9]

            # If this is in one of the language dirs we were reading.
            if subpath_language_dir in new_path_map:
                new_path = destination_documentation_dir + (
                    new_path_map[subpath_language_dir] + subpath[9:])

                if '.html' in file or '_images' in subpath:
                    if not os.path.exists(os.path.dirname(new_path)):
                        os.makedirs(os.path.dirname(new_path))

                if '.html' in file:
                    # Soup the body of the HTML file.
                    with open(os.path.join(subdir, file)) as original_html_file:
                        soup = BeautifulSoup(original_html_file, 'html.parser')

                    # Find the .document element.
                    document = soup.select('div.document')[0]

                    with open(new_path, 'w') as new_html_partial:
                        new_html_partial.write(document.encode("utf-8"))

                elif '_images' in subpath:
                    # Copy to images directory.
                    copyfile(os.path.join(subdir, file), new_path)


def book(original_documentation_dir, version, destination_documentation_dir):
    """
    Strip out the static and extract the body contents, ignoring the TOC,
    headers, and body.
    """
    # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
    # and transform them using a markdown library.
    for subdir, dirs, all_files in os.walk(original_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                original_documentation_dir):]
            new_path = '%s/%s/book/%s' % (destination_documentation_dir, version, subpath)

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


def models(original_documentation_dir, version, destination_documentation_dir):
    """
    Strip out the static and extract the body contents, headers, and body.
    """
    # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
    # and transform them using a markdown library.
    for subdir, dirs, all_files in os.walk(original_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                original_documentation_dir):]

            # Replace .md with .html.
            (name, extension) = os.path.splitext(subpath)
            if extension == '.md':
                subpath = name + '.html'

            new_path = '%s/%s/models%s' % (destination_documentation_dir, version, subpath)

            if '.md' in file or 'images' in subpath:
                if not os.path.exists(os.path.dirname(new_path)):
                    os.makedirs(os.path.dirname(new_path))

            if '.md' in file:
                # Convert the contents of the MD file.
                with open(os.path.join(subdir, file)) as original_md_file:
                    markdown_body = original_md_file.read()

                    with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                        # Strip out the wrapping HTML
                        new_html_partial.write(
                            '{% verbatim %}\n' + markdown.markdown(
                                unicode(markdown_body, 'utf-8'),
                                extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables']
                            ) + '\n{% endverbatim %}'
                        )

            elif 'images' in subpath:
                copyfile(os.path.join(subdir, file), new_path)
