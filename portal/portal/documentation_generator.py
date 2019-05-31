# -*- coding: utf-8 -*-

import os
import tempfile
import traceback
from urlparse import urlparse
import json
from subprocess import call
import shutil
from shutil import copyfile, copytree, rmtree
import re
import codecs
import requests
import sys
import inspect
import ast

from django.conf import settings
from bs4 import BeautifulSoup
import markdown
try:
    # NOTE(Varun): This will be imported in the case this is running on CI
    # and that Paddle was just built.
    from paddle import fluid
except:
    pass


from portal import menu_helper, portal_helper, url_helper
from management.commands.utils import sanitize_version
import sphinx_utils


MARKDOWN_EXTENSIONS = [
    'markdown.extensions.fenced_code',
    'markdown.extensions.tables',
    'pymdownx.superfences',
    'pymdownx.escapeall'
]


class DocumentationGenerator():
    GITHUB_REPO_URL = 'https://github.com/PaddlePaddle/Paddle/blob/'

    def __init__(self, source_dir, destination_dir, content_id, raw_version='develop', lang=None):
        self.source_dir = source_dir
        self.destination_dir = destination_dir

        if content_id == 'paddle-mobile':
            content_id = 'mobile'

        self.content_id = content_id

        self.lang = lang
        self.raw_version = raw_version
        self.version = sanitize_version(raw_version)


    def docs(self):
        """
        Strip out the static and extract the body contents, ignoring the TOC,
        headers, and body.
        """
        try:
            menu_path = menu_helper.get_menu(
                'docs', self.lang or 'en', self.version)[1]
        except IOError, e:
            menu_path = e[1]

        langs = [self.lang] if self.lang else ['en', 'zh']

        new_menu = None

        # Set up new_menu to indicate that we need to parse html to create new menu
        if not settings.SUPPORT_MENU_JSON:
            new_menu = { 'sections': [] }

        destination_dir = self.destination_dir
        for lang in langs:
            if not destination_dir:
                destination_dir = url_helper.get_full_content_path(
                    'docs', lang, self.version)[0]

            self.generated_dir = _get_new_generated_dir('docs', lang)

            if not new_menu:
                sphinx_utils.build_sphinx_index_from_menu(menu_path, lang)

            print "Use Sphinx comment: sphinx-build -b html -c %s %s %s" % (
                os.path.join(settings.SPHINX_CONFIG_DIR, lang), self.source_dir, self.generated_dir)

            call(['sphinx-build', '-b', 'html', '-c',
                os.path.join(settings.SPHINX_CONFIG_DIR, lang),
                self.source_dir, self.generated_dir])

        # Generate a menu from the rst root menu if it doesn't exist.
        if new_menu:
            # FORCEFULLY generate for both languages.
            for lang in (['en', 'zh'] if settings.ENV in ['production', 'staging'] else langs):
                sphinx_utils.create_sphinx_menu(
                    self.source_dir, 'docs', lang, self.version, new_menu,
                    _get_new_generated_dir(self.content_id, lang)
                )

        for lang in langs:
            if self.lang:
                lang_destination_dir = destination_dir
            else:
                lang_destination_dir = os.path.join(destination_dir, 'docs', lang, self.version)

            self.strip_sphinx_documentation(lang, lang_destination_dir)
            # shutil.rmtree(generated_dir)

        if new_menu:
            self.save_menu(new_menu, menu_path)
        else:
            for lang in (['en', 'zh'] if settings.ENV in ['production', 'staging'] else langs):
                sphinx_utils.remove_sphinx_menu(menu_path, lang)


    def strip_sphinx_documentation(self, lang, lang_destination_dir):
        # Go through each file, and if it is a .html, extract the .document object
        #   contents
        generated_dir = _get_new_generated_dir(self.content_id, lang)

        for subdir, dirs, all_files in os.walk(generated_dir):
            for file in all_files:
                subpath = os.path.join(subdir, file)[len(generated_dir):]

                if not subpath.startswith('/.') and not subpath.startswith(
                    '/_static') and not subpath.startswith('/_doctrees'):
                    new_path = lang_destination_dir + subpath

                    if '.html' in file or '_images' in subpath or '.txt' in file or '.json' in file:
                        if not os.path.exists(os.path.dirname(new_path)):
                            os.makedirs(os.path.dirname(new_path))

                    if '.html' in file:
                        # Soup the body of the HTML file.
                        # Check if this HTML was generated from Markdown
                        original_md_path = get_original_markdown_path(
                            self.source_dir, subpath[1:])

                        if original_md_path:
                            # If this html file was generated from Sphinx MD, we need to regenerate it using python's
                            # MD library.  Sphinx MD library is limited and doesn't support tables
                            self.markdown_file(original_md_path, self.version, '', new_path)

                            # Since we are ignoring SPHINX's generated HTML for MD files (and generating HTML using
                            # python's MD library), we must fix any image links that starts with 'src/'.
                            image_subpath = None

                            parent_paths = subpath.split('/')
                            if '' in parent_paths:
                                parent_paths.remove('')

                            image_subpath = ''

                            # -1 because we nest it 1 further levels? No idea.
                            for i in range(len(parent_paths) - 1):
                                image_subpath = image_subpath + '../'

                            # hardcode the sphinx '_images' dir
                            image_subpath += '_images'

                            with open(new_path) as original_html_file:
                                soup = BeautifulSoup(original_html_file, 'lxml')

                                prepare_internal_urls(soup, lang, self.version)

                                image_links = soup.find_all(
                                    'img', src=re.compile(r'^(?!http).*'))

                                if len(image_links) > 0:
                                    for image_link in image_links:
                                        image_file_name = os.path.basename(
                                            image_link['src'])

                                        if image_subpath:
                                            image_link['src'] = '%s/%s' % (
                                                image_subpath, image_file_name)
                                        else:
                                            image_link['src'] = '_images/%s' % (
                                                image_file_name)

                                    with open(new_path, 'w') as new_html_partial:
                                        new_html_partial.write(soup.encode("utf-8"))
                        else:
                            with open(os.path.join(subdir, file)) as original_html_file:
                                soup = BeautifulSoup(original_html_file, 'lxml')

                            document = None
                            # Find the .document element.
                            if self.version == '0.9.0':
                                document = soup.select('div.body')[0]
                            else:
                                document = soup.select('div.document')[0]

                            with open(new_path, 'w') as new_html_partial:
                                new_html_partial.write(
                                    self._conditionally_preprocess_document(
                                        document, soup, new_path, subpath
                                    ).encode("utf-8"))

                    elif '_images' in subpath or '.txt' in file or '.json' in file:
                        # Copy to images directory.
                        copyfile(os.path.join(subdir, file), new_path)


    def _get_repo_source_url_from_api(self, current_class, api_call):
        line_no = None

        api_title = api_call.contents[0]

        if api_call.name == 'h1':
            # The -1 prevents us from the c in .pyc
            module = os.path.splitext(current_class.__file__)[0] + '.py'

        else:
            api = getattr(current_class, api_title)

            if type(api).__name__ == 'module':
                module = os.path.splitext(api.__file__)[0] + '.py'
            else:
                node_definition = ast.ClassDef if inspect.isclass(api) else ast.FunctionDef

                if api.__module__ not in ['paddle.fluid.core', 'paddle.fluid.layers.layer_function_generator']:
                    module = os.path.splitext(sys.modules[api.__module__].__file__)[0] + '.py'

                    with open(module) as module_file:
                        module_ast = ast.parse(module_file.read())

                        for node in module_ast.body:
                            if isinstance(node, node_definition) and node.name == api_title:
                                line_no = node.lineno
                                break

                        # If we could not find it, we look at assigned objects.
                        if not line_no:
                            for node in module_ast.body:
                                if isinstance(node, ast.Assign) and api_title in [target.id for target in node.targets]:
                                    line_no = node.lineno
                                    break
                else:
                    module = os.path.splitext(current_class.__file__)[0] + '.py'

        url = self.GITHUB_REPO_URL + os.path.join(
            self.raw_version, module[module.rfind('python/paddle'):])

        if line_no:
            return url + '#L' + str(line_no)

        return url


    def _conditionally_preprocess_document(self, document, soup, path, subpath):
        """
        Takes a soup-ed document that is about to be written into final output.
        Any changes can be conditionally made to it.
        """
        # Determine if this is an API path, and specifically, if this is a path to
        # Chinese API.
        if self.version >= '1.2' and len(subpath.split('/')) == 3:
            is_chinese_api = subpath.startswith('/api_cn/')
            is_english_api = subpath.startswith('/api/')

            if (is_chinese_api or is_english_api) and (
                subpath.split('/')[-1] not in ['index_cn.html', 'index.html']):

                if is_chinese_api:
                    # Determine the class name.
                    current_class = sys.modules['.'.join(['paddle', document.find('h1').contents[0]])]

                    print 'Finding/building source for: ' + current_class.__file__

                for api_call in document.find_all(re.compile('^h(1|2|3)')):
                    if is_chinese_api:
                        url = self._get_repo_source_url_from_api(current_class, api_call)

                    # Create an element that wraps the heading level class or function
                    # name.
                    title_wrapper = soup.new_tag('div')
                    title_wrapper['class'] = 'api-wrapper'
                    api_call.insert_before(title_wrapper)
                    api_call.wrap(title_wrapper)

                    # NOTE: This path might be not unique in the system.
                    # Needs to be made tighter in future.
                    url_path = path[path.rfind('documentation/docs/'):]
                    content_id, lang, version = url_helper.get_parts_from_url_path(url_path)

                    # Now add a link on the same DOM wrapper of the heading to include
                    # a link to the expected English doc link.
                    lang_source_link_wrapper = soup.new_tag('div')
                    lang_source_link_wrapper['class'] = 'btn-group'

                    if is_chinese_api:
                        # Add a link to the GitHub source.
                        source_link = soup.new_tag('a', href=url)
                        source_link['target'] = '_blank'
                        source_link.string = 'Source'
                        source_link['class'] = 'btn btn-outline-info'
                        lang_source_link_wrapper.append(source_link)

                    # Toggle the URL based on which language it can change into.
                    if is_chinese_api:
                        url_path_parts = url_path.split('/')
                        page_path = os.path.join(
                            os.path.join(*url_path_parts[4:-1]).replace(
                               'api_cn', 'api'),
                            url_path_parts[-1].replace('_cn', '')
                        )
                    else:
                         url_path_split = os.path.splitext(url_path)
                         page_path = '/'.join(url_path_split[0].replace(
                            '/api/', '/api_cn/').split('/')[4:]) + '_cn' + url_path_split[1]

                    # Add a link to the alternative language's docs source.
                    lang_link = soup.new_tag('a', href=(
                        '/' + url_helper.get_page_url_prefix(
                            content_id, 'en'if is_chinese_api else 'zh', version)) + (

                        # Take everything after the version, and replace '_cn' in it.
                        '/' + page_path) + (

                        # This is usually the anchor bit.
                        api_call.find('a')['href']))

                    lang_link.string = 'English' if is_chinese_api else 'Chinese'
                    lang_link['class'] = 'btn btn-outline-secondary'
                    lang_source_link_wrapper.append(lang_link)

                    title_wrapper.append(lang_source_link_wrapper)

        return document


    def save_menu(self, menu, menu_path):
        if menu:
            menu_dir = os.path.dirname(menu_path)

            if not os.path.exists(menu_dir):
                os.makedirs(menu_dir)

            with open(menu_path, 'w') as menu_file:
                menu_file.write(json.dumps(menu, indent=4))

            # Because this only happens in production, and we do 'en' above temporarily.
            if not self.lang:
                alternative_menu_path = menu_helper.get_production_menu_path(
                    self.content_id, 'zh', self.version)

                menu_dir = os.path.dirname(alternative_menu_path)

                if not os.path.exists(menu_dir):
                    os.makedirs(menu_dir)

                copyfile(menu_path, alternative_menu_path)


    def models(self):
        """
        Strip out the static and extract the body contents, headers, and body.
        """
        destination_dir = self.destination_dir

        if not self.lang:
            original_destination_dir = destination_dir
            destination_dir = os.path.join(
                destination_dir, 'models', 'en', self.version)

        # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
        # and transform them using a markdown library.
        for subdir, dirs, all_files in os.walk(self.source_dir):
            # Avoid parsing PaddlePaddle.org folder
            if 'PaddlePaddle.org' in subdir:
                continue

            for file in all_files:
                subpath = os.path.join(subdir, file)[len(self.source_dir):]

                # Replace .md with .html.
                (name, extension) = os.path.splitext(subpath)
                if extension == '.md':
                    subpath = name + '.html'

                new_path = '%s/%s' % (destination_dir, subpath)

                if '.md' in file or 'images' in subpath:
                    if not os.path.exists(os.path.dirname(new_path)):
                        os.makedirs(os.path.dirname(new_path))

                if '.md' in file:
                    # Convert the contents of the MD file.
                    with open(os.path.join(subdir, file)) as original_md_file:
                        print("Generating file: %s" % subpath)
                        markdown_body = sanitize_markdown(original_md_file.read())

                        # Preserve all formula
                        formula_map = {}
                        markdown_body = self.reserve_formulas(markdown_body, formula_map)

                        with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                            # Strip out the wrapping HTML
                            converted_content = markdown.markdown(
                                unicode(markdown_body, 'utf-8'),
                                extensions=MARKDOWN_EXTENSIONS
                            )

                            github_url = 'https://github.com/PaddlePaddle/models/tree/'

                            soup = BeautifulSoup(converted_content, 'lxml')

                            prepare_internal_urls(soup, self.lang, self.version)

                            # Insert the preserved formulas
                            markdown_equation_placeholders = soup.select('.markdown-equation')
                            for equation in markdown_equation_placeholders:
                                equation.string = formula_map[equation.get('id')]

                            all_local_links = soup.select('a[href^=%s]' % github_url)
                            for link in all_local_links:
                                link_path, md_extension = os.path.splitext(link['href'])

                                # Remove the github link and version.
                                link_path = link_path.replace(github_url, '')
                                link_path = re.sub(r"^v?[0-9]+\.[0-9]+\.[0-9]+/|^develop/", '', link_path)
                                link['href'] = _update_link_path(link_path, md_extension)

                            # Note: Some files have links to local md files. Change those links to local html files
                            all_local_links_with_relative_path = soup.select('a[href^=%s]' % './')
                            for link in all_local_links_with_relative_path:
                                link_path, md_extension = os.path.splitext(link['href'])
                                link['href'] = _update_link_path(link_path, md_extension)

                            try:
                                # NOTE: The 6:-7 removes the opening and closing body tag.
                                new_html_partial.write('{% verbatim %}\n' + unicode(
                                    str(soup.select('body')[0])[6:-7], 'utf-8'
                                ) + '\n{% endverbatim %}')
                            except:
                                print 'Cannot generated a page for: ' + subpath


                elif 'images' in subpath:
                    shutil.copyfile(os.path.join(subdir, file), new_path)

        if not self.lang:
            shutil.copytree(destination_dir, os.path.join(
                original_destination_dir, 'models', 'zh', self.version))

        return destination_dir


    def mobile(self):
        """
        Simply convert the markdown to HTML.
        """
        destination_dir = self.destination_dir

        if not self.lang:
            original_destination_dir = destination_dir
            destination_dir = os.path.join(
                destination_dir, 'mobile', 'en', self.version)

        # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
        # and transform them using a markdown library.
        for subdir, dirs, all_files in os.walk(self.source_dir):
            # Avoid parsing PaddlePaddle.org folder
            if 'PaddlePaddle.org' in subdir:
                continue

            for file in all_files:
                subpath = os.path.join(subdir, file)[len(self.source_dir):]

                # Replace .md with .html.
                (name, extension) = os.path.splitext(subpath)
                if extension == '.md':
                    subpath = name + '.html'

                new_path = '%s/%s' % (destination_dir, subpath)

                if '.md' in file or 'image' in subpath:
                    if not os.path.exists(os.path.dirname(new_path)):
                        os.makedirs(os.path.dirname(new_path))

                if '.md' in file:
                    # Convert the contents of the MD file.
                    with open(os.path.join(subdir, file)) as original_md_file:
                        print("Generating file: %s" % subpath)

                        markdown_body = sanitize_markdown(original_md_file.read())

                        with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                            # Strip out the wrapping HTML
                            html = markdown.markdown(
                                unicode(markdown_body, 'utf-8'),
                                extensions=MARKDOWN_EXTENSIONS
                            )

                            soup = BeautifulSoup(html, 'lxml')

                            prepare_internal_urls(soup, self.lang, self.version)

                            all_local_links = soup.select('a[href^="."]')
                            for link in all_local_links:
                                link_path, md_extension = os.path.splitext(link['href'])
                                link['href'] = _update_link_path(link_path, md_extension)

                            # There are several links to the Paddle folder.
                            # We first extract those links and update them according to the languages.
                            github_url = 'https://github.com/PaddlePaddle/Paddle/blob/develop/doc/mobile'
                            all_paddle_doc_links = soup.select('a[href^=%s]' % github_url)
                            for link in all_paddle_doc_links:
                                link_path, md_extension = os.path.splitext(link['href'])
                                link_path = _update_link_path(link_path, md_extension)
                                if link_path.endswith('cn.html'):
                                    link_path = link_path.replace(github_url, '/docs/develop/mobile/zh/')
                                elif link_path.endswith('en.html'):
                                    link_path = link_path.replace(github_url, '/docs/develop/mobile/en/')

                                link['href'] = link_path

                            new_html_partial.write(
                                '{% verbatim %}\n' + unicode(str(soup), 'utf-8') + '\n{% endverbatim %}')

                elif 'image' in subpath:
                    shutil.copyfile(os.path.join(subdir, file), new_path)

        if not self.lang:
            shutil.copytree(destination_dir, os.path.join(
                original_destination_dir, 'mobile', 'zh', self.version))

        return destination_dir


    def book(self):
        """
        Strip out the static and extract the body contents, headers, and body.
        """
        # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
        # and transform them using a markdown library.
        destination_dir = self.destination_dir

        # Remove old generated docs directory
        if not self.lang:
            original_destination_dir = destination_dir
            destination_dir = os.path.join(destination_dir, 'book', 'en', self.version)

        if os.path.exists(destination_dir) and os.path.isdir(destination_dir):
            shutil.rmtree(destination_dir)

        if os.path.exists(os.path.dirname(self.source_dir)):
            for subdir, dirs, all_files in os.walk(self.source_dir):
                # Avoid parsing PaddlePaddle.org folder
                if 'PaddlePaddle.org' in subdir:
                    continue

                for file in all_files:
                    subpath = os.path.join(subdir, file)[len(self.source_dir):]

                    # Replace .md with .html, and 'README' with 'index'.
                    (name, extension) = os.path.splitext(subpath)
                    if extension == '.md':
                        if 'README' in name:
                            subpath = name[:name.index('README')] + 'index' + name[name.index('README') + 6:] + '.html'
                        else:
                            subpath = name + '.html'

                    new_path = '%s/%s' % (destination_dir, subpath)

                    if '.md' in file or 'image/' in subpath:
                        if not os.path.exists(os.path.dirname(new_path)):
                            os.makedirs(os.path.dirname(new_path))

                    if '.md' in file:
                        print("Generating file: %s" % subpath)

                        # Convert the contents of the MD file.
                        with open(os.path.join(subdir, file)) as original_md_file:
                            markdown_body = sanitize_markdown(original_md_file.read())

                        # Mathjax formula like $n$ would cause the conversion from markdown to html
                        # mal-formatted. So we first store the existing formulas to formula_map and replace
                        # them with <span></span>. After the conversion, we put them back.
                        markdown_body = unicode(str(markdown_body), 'utf-8')
                        formula_map = {}
                        markdown_body = self.reserve_formulas(markdown_body, formula_map)

                        # NOTE: This ignores the root index files.
                        if len(markdown_body) > 0:
                            with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                                converted_content = markdown.markdown(markdown_body,
                                    extensions=MARKDOWN_EXTENSIONS)

                                soup = BeautifulSoup(converted_content, 'lxml')

                                markdown_equation_placeholders = soup.select('.markdown-equation')
                                for equation in markdown_equation_placeholders:
                                    equation.string = formula_map[equation.get('id')]

                                prepare_internal_urls(soup, self.lang, self.version)

                                try:
                                    # NOTE: The 6:-7 removes the opening and closing body tag.
                                    new_html_partial.write('{% verbatim %}\n' + unicode(
                                        str(soup.select('body')[0])[6:-7], 'utf-8'
                                    ) + '\n{% endverbatim %}')
                                except:
                                    print 'Cannot generated a page for: ' + subpath

                    elif 'image/' in subpath:
                        shutil.copyfile(os.path.join(subdir, file), new_path)

            if not self.lang:
                shutil.copytree(destination_dir, os.path.join(
                    original_destination_dir, 'book', 'zh', self.version))

            # Generate a menu.json in the source directory.
            # NOTE: Remove this next segment once menu.json is available.
            menu_json_path = os.path.join(self.source_dir, 'menu.json')

            if not settings.SUPPORT_MENU_JSON:
                new_menu = { 'sections': [
                    # {
                    #     "title":{
                    #         "en":"Deep Learning 101",
                    #         "zh":"Deep Learning 101"
                    #     },
                    #     'sections': []
                    # }
                ] }
                with open(os.path.join(self.source_dir, '.tools/templates/index.html.json'), 'r') as en_menu_file:
                    en_menu = json.loads(en_menu_file.read())
                    # new_menu['sections'][0]['sections'] = [
                    new_menu['sections'] = [
                        {
                            'title': { 'en': c['name'] },
                            'link': { 'en': c['link'][2:] },
                        } for c in en_menu['chapters']
                    ]

                with open(os.path.join(self.source_dir, '.tools/templates/index.cn.html.json'), 'r') as zh_menu_file:
                    zh_menu = json.loads(zh_menu_file.read())
                    # for index, section in enumerate(new_menu['sections'][0]['sections']):
                    for index, section in enumerate(new_menu['sections']):
                        zh_menu_item = zh_menu['chapters'][index]
                        # new_menu['sections'][0]['sections'][index]['title']['zh'] = zh_menu_item['name']
                        # new_menu['sections'][0]['sections'][index]['link']['zh'] = zh_menu_item['link']
                        new_menu['sections'][index]['title']['zh'] = zh_menu_item['name']
                        new_menu['sections'][index]['link']['zh'] = zh_menu_item['link'][2:]

                with open(menu_json_path, 'w') as menu_file:
                    menu_file.write(json.dumps(new_menu, indent=4))

        else:
            raise Exception('Cannot generate book, directory %s does not exists.' % source_dir)

        return destination_dir


    def visualdl(self):
        """
        Given a VisualDL doc directory, invoke a script to generate docs using Sphinx
        and after parsing the code base based on given config, into an output dir.
        """
        try:
            menu_path = menu_helper.get_menu(
                'visualdl', self.lang or 'en', self.version)[1]
        except IOError, e:
            menu_path = e[1]

        if os.path.exists(os.path.dirname(self.source_dir)):
            script_path = os.path.join(
                settings.BASE_DIR, '../scripts/deploy/generate_visualdl_docs.sh')

            if os.path.exists(os.path.dirname(script_path)):
                generated_dir = _get_new_generated_dir('visualdl')

                if self.lang:
                    call([script_path, self.source_dir, generated_dir, self.lang])
                    langs = [self.lang]
                else:
                    call([script_path, self.source_dir, generated_dir])
                    langs = ['en', 'zh']

                new_menu = None

                # Set up new_menu to indicate that we need to parse html to create new menu
                if not settings.SUPPORT_MENU_JSON:
                    new_menu = { 'sections': [] }

                # Generate a menu from the rst root menu if it doesn't exist.
                if new_menu:
                    for lang in (['en', 'zh'] if settings.ENV in ['production', 'staging'] else langs):
                        sphinx_utils.create_sphinx_menu(
                            self.source_dir, 'visualdl', lang, self.version, new_menu,
                            _get_new_generated_dir(self.content_id, lang)
                        )

                for lang in langs:
                    if self.lang:
                        lang_destination_dir = destination_dir
                    else:
                        lang_destination_dir = os.path.join(
                            self.destination_dir, 'visualdl', lang, self.version)

                    self.strip_sphinx_documentation(lang, lang_destination_dir)

                if new_menu:
                    self.save_menu(new_menu, menu_path)
                else:
                    for lang in (['en', 'zh'] if settings.ENV in ['production', 'staging'] else langs):
                        sphinx_utils.remove_sphinx_menu(menu_path, lang)

            else:
                raise Exception('Cannot find script located at %s.' % script_path)
        else:
            raise Exception('Cannot generate documentation, directory %s does not exists.' % self.source_dir)


    def markdown_file(self, source_markdown_file, version, tmp_dir, new_path=None):
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
            markdown_body = sanitize_markdown(original_md_file.read())

            # Preserve all formula
            formula_map = {}
            markdown_body = self.reserve_formulas(markdown_body, formula_map)

            with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                converted_content = markdown.markdown(
                    unicode(markdown_body, 'utf-8'),
                    extensions=MARKDOWN_EXTENSIONS
                )

                soup = BeautifulSoup(converted_content, 'lxml')

                # Insert the preserved formulas
                markdown_equation_placeholders = soup.select('.markdown-equation')
                for equation in markdown_equation_placeholders:
                    equation.string = formula_map[equation.get('id')]

                # Strip out the wrapping HTML
                new_html_partial.write(
                    '{% verbatim %}\n' + unicode(
                        str(soup.select('body')[0])[6:-7], 'utf-8'
                    ) + '\n{% endverbatim %}'
                )


    def reserve_formulas(self, markdown_body, formula_map, only_reserve_double_dollar=False):
        """
        Store the math formulas to formula_map before markdown conversion
        """
        place_holder = '<span class="markdown-equation" id="equation-%s"></span>'


        markdown_body_list = markdown_body.split('\n')

        math = []
        for i in range(len(markdown_body_list)):
            body = markdown_body_list[i].strip(' ')
            # if body.startswith('`') and body.endswith('`'):
            #     continue
            #
            # if only_reserve_double_dollar:
            #     m = re.findall('(\$\$[^\$]+\$\$)', body)
            # else:
            #     m = re.findall('(\$\$?[^\$]+\$?\$)', body)

            if only_reserve_double_dollar:
                m = re.findall('(\`?\$\$[^\$\n]+\$\$\`?)', body)
            else:
                m = re.findall('(\`?\$\$?[^\$\n]+\$?\$\`?)', body)
            math += m

        for i in xrange(len(math)):
            formula_map['equation-' + str(i)] = math[i].strip('`')
            markdown_body = markdown_body.replace(math[i], place_holder % i)

        return markdown_body


    def run(self):
        print 'Processing docs at %s to %s' % (
            self.source_dir, self.destination_dir)

        getattr(self, self.content_id)()


# Pure utils.
def _get_new_generated_dir(content_id, lang=None):
    generated_dir = '/tmp/%s' % content_id

    if lang:
        generated_dir = generated_dir + '/' + lang

    if not os.path.exists(generated_dir):
        try:
            os.makedirs(generated_dir)
        except:
            generated_dir = tempfile.mkdtemp()

    return generated_dir


def sanitize_markdown(markdown_body):
    """
    There are some symbols used in the markdown body, which when go through Markdown -> HTML
    conversion, break. This does a global replace on markdown strings for these symbols.
    """
    return markdown_body.replace(
        # This is to solve the issue where <s> and <e> are interpreted as HTML tags
        '&lt;', '<').replace(
        '&gt;', '>').replace(
        '\<s>', '&lt;s&gt;').replace(
        '\<e>', '&lt;e&gt;')


def get_original_markdown_path(original_documentation_dir, file):
    """
    Finds the path of the original MD file that generated the html file located at "path"
    :param original_documentation_dir:
    :param path:
    :param subpath_language_dir:
    :param file:
    :return:
    """
    filename, _ = os.path.splitext(file)
    original_file_path = '%s/%s.md' % (original_documentation_dir, filename)

    if os.path.isfile(original_file_path):
        return original_file_path
    else:
        return None


def prepare_internal_urls(soup, lang, version):
    """
    Replaces references to files in other repos with the "correct" links.
    """
    all_internal_links = soup.select('a[repo]')

    for link in all_internal_links:
        content_id = link['repo'].lower()

        if link['version']:
            version = link['version']

        link['href'] = url_helper.get_url_path(
            url_helper.get_page_url_prefix(content_id, lang, version),
            link['href']
        )

        del link['repo']


def _update_link_path(link_path, md_extension):
    if link_path.endswith('/'):
        link_path += 'README.html'
    elif md_extension == '.md':
        link_path += '.html'
    elif md_extension == '':
        link_path += '/README.html'
    else:
        link_path += md_extension

    return link_path
