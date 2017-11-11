import os
import re
import shutil
import codecs
from subprocess import call

from bs4 import BeautifulSoup
from django.conf import settings
import markdown
import re

from deploy.operators import generate_operators_page

MARKDOWN_EXTENSIONS = [
    'markdown.extensions.tables',
    'pymdownx.superfences',
    'pymdownx.escapeall'
]


def generate_paddle_docs(original_documentation_dir, output_dir_name):
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

        if os.path.exists(os.path.dirname(script_path)):
            call([script_path, original_documentation_dir, destination_dir])

            return destination_dir
        else:
            raise Exception('Cannot find script located at %s.' % script_path)
    else:
        raise Exception('Cannot generate documentation, directory %s does not exists.' % original_documentation_dir)


def generate_models_docs(original_documentation_dir, output_dir_name):
    """
    Strip out the static and extract the body contents, headers, and body.
    """
    # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
    # and transform them using a markdown library.
    destination_documentation_dir = _get_destination_documentation_dir(output_dir_name)

    for subdir, dirs, all_files in os.walk(original_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                original_documentation_dir):]

            # Replace .md with .html.
            (name, extension) = os.path.splitext(subpath)
            if extension == '.md':
                subpath = name + '.html'

            new_path = '%s/%s' % (destination_documentation_dir, subpath)

            if '.md' in file or 'images' in subpath:
                if not os.path.exists(os.path.dirname(new_path)):
                    os.makedirs(os.path.dirname(new_path))

            if '.md' in file:
                # Convert the contents of the MD file.
                with open(os.path.join(subdir, file)) as original_md_file:
                    markdown_body = original_md_file.read()

                    # This is to solve the issue where <s> and <e> are interpreted as HTML tags
                    markdown_body = markdown_body.replace('\<s>', '&lt;s&gt;').replace('\<e>', '&lt;e&gt;')

                    with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                        # Strip out the wrapping HTML
                        html = markdown.markdown(
                            unicode(markdown_body, 'utf-8'),
                            extensions=MARKDOWN_EXTENSIONS
                        )

                        github_url = 'https://github.com/PaddlePaddle/models/tree/'
                        soup = BeautifulSoup(html, 'lxml')
                        all_local_links = soup.select('a[href^=%s]' % github_url)
                        for link in all_local_links:
                            link_path, md_extension = os.path.splitext(link['href'])

                            # Remove the github link and version.
                            link_path = link_path.replace(github_url, '')
                            link_path = re.sub(r"^v?[0-9]+\.[0-9]+\.[0-9]+/|^develop/", '', link_path)

                            # TODO[thuan]:  Since all markdown are named README.md, we need to hardcode this for now, regardless of language.
                            # We need to communicate this with the team to get it corrected
                            if not md_extension:
                                link['href'] = link_path + '/README.html'

                        try:
                            # NOTE: The 6:-7 removes the opening and closing body tag.
                            new_html_partial.write('{% verbatim %}\n' + unicode(
                                str(soup.select('body')[0])[6:-7], 'utf-8'
                            ) + '\n{% endverbatim %}')
                        except:
                            print 'Cannot generated a page for: ' + subpath


            elif 'images' in subpath:
                shutil.copyfile(os.path.join(subdir, file), new_path)

    return destination_documentation_dir


def generate_mobile_docs(original_documentation_dir, output_dir_name):
    """
    Simply convert the markdown to HTML.
    """
    # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
    # and transform them using a markdown library.
    destination_documentation_dir = _get_destination_documentation_dir(output_dir_name)

    for subdir, dirs, all_files in os.walk(original_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                original_documentation_dir):]

            # Replace .md with .html.
            (name, extension) = os.path.splitext(subpath)
            if extension == '.md':
                subpath = name + '.html'

            new_path = '%s/%s' % (destination_documentation_dir, subpath)

            if '.md' in file or 'image' in subpath:
                if not os.path.exists(os.path.dirname(new_path)):
                    os.makedirs(os.path.dirname(new_path))

            if '.md' in file:
                # Convert the contents of the MD file.
                with open(os.path.join(subdir, file)) as original_md_file:
                    markdown_body = original_md_file.read()

                    with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                        # Strip out the wrapping HTML
                        html = markdown.markdown(
                            unicode(markdown_body, 'utf-8'),
                            extensions=MARKDOWN_EXTENSIONS
                        )

                        # TODO: Go through all URLs, and if their href matches a
                        # pattern of the Github repo pulled from Mobile,
                        # Replace it's .md extension with .html.
                        soup = BeautifulSoup(html, 'lxml')
                        all_local_links = soup.select('a[href^="."]')

                        for link in all_local_links:
                            # Since this is a Github repo, the default page should
                            # pick from a README.md instead of the webserver
                            # expected index.html.
                            if link['href'].endswith('/'):
                                link['href'] += 'README.md'

                            link_path, md_extension = os.path.splitext(link['href'])

                            if md_extension == '.md':
                                link['href'] = link_path + '.html'

                        new_html_partial.write(
                            '{% verbatim %}\n' + unicode(str(soup), 'utf-8') + '\n{% endverbatim %}')

            elif 'image' in subpath:
                shutil.copyfile(os.path.join(subdir, file), new_path)

    return destination_documentation_dir


def reserve_formulas(markdown_body, formula_map):
    """
    Store the math formulas to formula_map before markdown conversion
    """
    place_holder = '<span class="markdown-equation" id="equation-%s"></span>'
    m = re.findall('(\$\$?[^\$]+\$?\$)', markdown_body)
    for i in xrange(len(m)):
        formula_map['equation-' + str(i)] = m[i]
        markdown_body = markdown_body.replace(m[i], place_holder % i)

    return markdown_body


def generate_book_docs(original_documentation_dir, output_dir_name):
    """
    Strip out the static and extract the body contents, headers, and body.
    """
    # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
    # and transform them using a markdown library.
    destination_documentation_dir = _get_destination_documentation_dir(output_dir_name)

    # Remove old generated docs directory
    if os.path.exists(destination_documentation_dir) and os.path.isdir(destination_documentation_dir):
        shutil.rmtree(destination_documentation_dir)

    if os.path.exists(os.path.dirname(original_documentation_dir)):
        for subdir, dirs, all_files in os.walk(original_documentation_dir):
            for file in all_files:
                subpath = os.path.join(subdir, file)[len(
                    original_documentation_dir):]

                # Replace .md with .html, and 'README' with 'index'.
                (name, extension) = os.path.splitext(subpath)
                if extension == '.md':
                    if 'README' in name:
                        subpath = name[:name.index('README')] + 'index' + name[name.index('README') + 6:] + '.html'
                    else:
                        subpath = name + '.html'

                new_path = '%s/%s' % (destination_documentation_dir, subpath)

                if '.md' in file or 'image/' in subpath:
                    if not os.path.exists(os.path.dirname(new_path)):
                        os.makedirs(os.path.dirname(new_path))

                if '.md' in file:
                    # Convert the contents of the MD file.
                    with open(os.path.join(subdir, file)) as original_md_file:
                        markdown_body = original_md_file.read()

                    # Mathjax formula like $n$ would cause the conversion from markdown to html
                    # mal-formatted. So we first store the existing formulas to formula_map and replace
                    # them with <span></span>. After the conversion, we put them back.
                    markdown_body = unicode(str(markdown_body), 'utf-8')
                    formula_map = {}
                    markdown_body = reserve_formulas(markdown_body, formula_map)

                    # NOTE: This ignores the root index files.
                    if len(markdown_body) > 0:
                        with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                            converted_content = markdown.markdown(markdown_body,
                                extensions=MARKDOWN_EXTENSIONS)

                            soup = BeautifulSoup(converted_content, 'lxml')
                            markdown_equation_placeholders = soup.select('.markdown-equation')

                            for equation in markdown_equation_placeholders:
                                equation.string = formula_map[equation.get('id')]

                            try:
                                # NOTE: The 6:-7 removes the opening and closing body tag.
                                new_html_partial.write('{% verbatim %}\n' + unicode(
                                    str(soup.select('body')[0])[6:-7], 'utf-8'
                                ) + '\n{% endverbatim %}')
                            except:
                                print 'Cannot generated a page for: ' + subpath

                elif 'image/' in subpath:
                    shutil.copyfile(os.path.join(subdir, file), new_path)

    else:
        raise Exception('Cannot generate book, directory %s does not exists.' % original_documentation_dir)

    return destination_documentation_dir


def generate_blog_docs(original_documentation_dir, output_dir_name):
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


def _get_destination_documentation_dir(output_dir_name):
    documentation_dir = '%s/%s' % (settings.GENERATED_DOCS_DIR, output_dir_name)
    if not os.path.exists(documentation_dir):
        os.makedirs(documentation_dir)
    return documentation_dir
