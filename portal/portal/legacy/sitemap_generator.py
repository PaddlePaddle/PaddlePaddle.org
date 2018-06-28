# -*- coding: utf-8 -*-
import os
import json
from collections import OrderedDict
from django.conf import settings
from bs4 import BeautifulSoup
from portal.portal_helper import Content


class SphinxContent:
    PADDLE = 'paddle'
    PADDLE_API = 'api'
    VISUALDL = 'visualdl'


def paddle_sphinx_fluid_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    """
    Generates a sitemap for all languages for the paddle documentation.
    """
    print 'Generating sitemap for Paddle Fluid'
    parent_path_map = { 'en': '/fluid/en/html/',
                        'zh': '/fluid/cn/html/' }
    output_dir_name = output_dir_name + '/fluid'
    _paddle_sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name,
                           parent_path_map)


def paddle_sphinx_v2v1_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    """
    Generates a sitemap for all languages for the paddle documentation.
    """
    print 'Generating sitemap for Paddle V2V1'
    parent_path_map = { 'en': '/v2/en/html/',
                        'zh': '/v2/cn/html/' }
    _paddle_sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name,
                           parent_path_map)


def _paddle_sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name, parent_path_map):
    """
    Generates a sitemap for all languages for the paddle documentation.
    """
    versioned_dest_dir = get_destination_documentation_dir(version, output_dir_name)

    for lang, parent_path in parent_path_map.items():
        sitemap = None
        # Using the index.html of the generated Sphinx HTML documentation,
        # separately for each language, generate a sitemap.
        index_html_path = '%s/%s/index.html' % (generated_documentation_dir, parent_path)
        sitemap = _create_paddle_sphinx_site_map_from_index(index_html_path, lang, Content.DOCUMENTATION, output_dir_name)
        _write_sphinx_sitemap(sitemap, versioned_dest_dir, lang)


def paddle_api_sphinx_fluid_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    """
    Generates a sitemap for all languages for the paddle documentation.
    """
    print 'Generating sitemap for Paddle fluid API'
    parent_path_map = { 'en': '/fluid/api/en/html/',
                        'zh': '/fluid/api/cn/html/' }
    output_dir_name = output_dir_name + '/fluid'
    _paddle_api_sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name, parent_path_map)


def paddle_api_sphinx_v2v1_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    """
    Generates a sitemap for all languages for the paddle documentation.
    """
    versioned_dest_dir = get_destination_documentation_dir(version, output_dir_name)
    print 'Generating sitemap for Paddle V2V1 API'
    parent_path_map = { 'en': '/v2/api/en/html/',
                        'zh': '/v2/api/cn/html/' }
    _paddle_api_sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name, parent_path_map)


def _paddle_api_sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name, parent_path_map):
    """
    Generates a sitemap for all languages for the paddle documentation.
    """
    versioned_dest_dir = get_destination_documentation_dir(version, output_dir_name)
    for lang, parent_path in parent_path_map.items():
        sitemap = None
        # Using the index.html of the generated Sphinx HTML documentation,
        # separately for each language, generate a sitemap.
        index_html_path = '%s/%s/index.html' % (generated_documentation_dir, parent_path)

        if lang == 'en':
            sitemap = _create_paddle_sphinx_site_map_from_index(index_html_path, lang, Content.API, output_dir_name)
            _write_sphinx_sitemap(sitemap, versioned_dest_dir, lang)

            # Make a copy of EN documentation for now, since we only have API docs in english
            # We override the link language prefix
            # TODO(thuan): Fix this once we have chinese API documentation
            sitemap = _create_paddle_sphinx_site_map_from_index(index_html_path, 'zh', Content.API, output_dir_name, 'en')
            _write_sphinx_sitemap(sitemap, versioned_dest_dir, 'zh')


def visualdl_sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    """
    Generates a sitemap for all languages for the paddle documentation.
    """
    versioned_dest_dir = get_destination_documentation_dir(version, output_dir_name)

    print 'Generating sitemap for VisualDL'

    parent_path_map = { 'en': '/en/html/',
                        'zh': '/cn/html/' }

    for lang, parent_path in parent_path_map.items():
        sitemap = None
        # Using the index.html of the generated Sphinx HTML documentation,
        # separately for each language, generate a sitemap.
        index_html_path = '%s/%s/index.html' % (generated_documentation_dir, parent_path)
        sitemap = _create_visualdl_sphinx_site_map_from_index(index_html_path, lang, output_dir_name)
        _write_sphinx_sitemap(sitemap, versioned_dest_dir, lang)


def _sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name, sphinx_content):
    """
    Generates a sitemap for all languages for the paddle documentation.
    """
    versioned_dest_dir = get_destination_documentation_dir(version, output_dir_name)

    print 'Generating sitemap for %s' % sphinx_content

    parent_path_map = { 'en': '/en/html/',
                        'zh': '/cn/html/' }

    if version == '0.9.0':
        parent_path_map = { 'en': '/doc/',
                            'zh': '/doc_cn/'}

    for lang, parent_path in parent_path_map.items():
        sitemap = None
        # Using the index.html of the generated Sphinx HTML documentation,
        # separately for each language, generate a sitemap.
        index_html_path = '%s/%s/index.html' % (generated_documentation_dir, parent_path)

        if sphinx_content == SphinxContent.PADDLE:
            sitemap = _create_paddle_sphinx_site_map_from_index(index_html_path, lang, Content.DOCUMENTATION, output_dir_name)
            _write_sphinx_sitemap(sitemap, versioned_dest_dir, lang)
        elif sphinx_content == SphinxContent.PADDLE_API:
            if lang == 'en':
                sitemap = _create_paddle_sphinx_site_map_from_index(index_html_path, lang, Content.API, output_dir_name)
                _write_sphinx_sitemap(sitemap, versioned_dest_dir, lang)

                # Make a copy of EN documentation for now, since we only have API docs in english
                # We override the link language prefix
                # TODO(thuan): Fix this once we have chinese API documentation
                sitemap = _create_paddle_sphinx_site_map_from_index(index_html_path, 'zh', Content.API, output_dir_name, 'en')
                _write_sphinx_sitemap(sitemap, versioned_dest_dir, 'zh')
        elif sphinx_content == SphinxContent.VISUALDL:
            sitemap = _create_visualdl_sphinx_site_map_from_index(index_html_path, lang, output_dir_name)
            _write_sphinx_sitemap(sitemap, versioned_dest_dir, lang)


def _write_sphinx_sitemap(sitemap, versioned_dest_dir, lang):
    # Write the sitemap into the specific content directory.
    if sitemap:
        sitemap_ouput_path = get_sitemap_destination_path(versioned_dest_dir, lang)
        with open(sitemap_ouput_path, 'w') as outfile:
            json.dump(sitemap, outfile)


def _create_paddle_sphinx_site_map_from_index(index_html_path, language, content_id, output_dir_name, link_language_prefix=None):
    """
    Given an index.html generated from running Sphinx on a doc directory, parse
    the HTML tree to get the links from the navigation menu.

    Eg. creates Paddle doc TOC from HTML navigation.  Example of HTML:
      <nav class="doc-menu-vertical" role="navigation">
        <ul>
          <li class="toctree-l1">
            <a class="reference internal" href="getstarted/index_en.html">GET STARTED</a>
            <ul>
              <li class="toctree-l2">
                <a class="reference internal" href="getstarted/build_and_install/index_en.html">Install and Build</a>
                <ul>
                  <li class="toctree-l3">
                    <a class="reference internal" href="getstarted/build_and_install/docker_install_en.html">PaddlePaddle in Docker Containers</a>
                  </li>
                  <li class="toctree-l3">
                    <a class="reference internal" href="getstarted/build_and_install/build_from_source_en.html">Installing from Sources</a>
                  </li>
                </ul>
              </li>
            </ul>
          </li>
          <li class="toctree-l1">
            <a class="reference internal" href="howto/index_en.html">HOW TO</a>
          </li>
        </ul>
      </nav>
    """

    allow_parent_links = True
    title_en = 'Documentation'
    title_zh = '使用文档'

    if content_id == Content.API:
        allow_parent_links = False  # We do not allow parent links for API section
        title_en = 'API'
        title_zh = 'API'

    with open(index_html_path) as html:
        chapters = []

        sitemap = OrderedDict()
        sitemap['title'] = OrderedDict( { 'en': title_en, 'zh': title_zh} )
        sitemap['sections'] = chapters

        navs = BeautifulSoup(html, 'lxml').findAll('nav', class_='doc-menu-vertical')

        if len(navs) > 0:
            chapters_container = navs[0].find('ul', recursive=False)
            if chapters_container:

                for chapter in chapters_container.find_all('li', recursive=False):
                    _create_sphinx_site_map(chapters, chapter, language, content_id, output_dir_name, allow_parent_links, link_language_prefix)
        else:
            print 'Cannot generate sphinx sitemap, nav.doc-menu-vertical not found in %s' % index_html_path

        return sitemap


def _create_visualdl_sphinx_site_map_from_index(index_html_path, language, output_dir_name):
    with open(index_html_path) as html:
        chapters = []

        sitemap = OrderedDict()
        sitemap['title'] = OrderedDict( { 'en': 'Documentation', 'zh': '文档'} )
        sitemap['sections'] = chapters

        navs = BeautifulSoup(html, 'lxml').findAll('nav', class_='doc-menu-vertical')

        if len(navs) > 0:
            chapters_container = navs[0].find('ul', recursive=True)
            if chapters_container:

                for chapter in chapters_container.find_all('li', recursive=False):
                    _create_sphinx_site_map(chapters, chapter, language, Content.VISUALDL, output_dir_name, allow_parent_links=False)
        else:
            print 'Cannot generate sphinx sitemap, nav.wy-nav-side not found in %s' % index_html_path

        return sitemap


def _create_sphinx_site_map(parent_list, node, language, content_id, output_dir_name, allow_parent_links=True, link_language_prefix=None):
    """
    Recursive function to append links to a new parent list object by going down the
    nested lists inside the HTML, using BeautifulSoup tree parser.
    """
    if node:
        node_dict = OrderedDict()
        if parent_list != None:
            parent_list.append(node_dict)

        sections = node.findAll('ul', recursive=False)

        first_link = node.find('a')
        if first_link:
            link_language = link_language_prefix if link_language_prefix else language
            link_url = '/%s/%s/%s' % (output_dir_name, link_language, first_link['href'])
            node_dict['title'] = OrderedDict({ language: first_link.text })

            if allow_parent_links:
                # If we allow parent links, then we will add the link to the parent no matter what
                node_dict['link'] = OrderedDict({language: link_url})
            elif not sections:
                # If parent links are not allowed, and the parent does not have children then add a link
                node_dict['link'] = OrderedDict({ language: link_url})

        for section in sections:
            sub_sections = section.findAll('li', recursive=False)

            if len(sub_sections) > 0:
                node_dict['sections'] = []

                for sub_section in sub_sections:
                    _create_sphinx_site_map(node_dict['sections'], sub_section, language, content_id, output_dir_name, allow_parent_links, link_language_prefix)


def inject_operators_link(sitemap, lang):
    # Iterate through the sitemap, and insert "Operators" under the API section.
    sections = None
    for section in sitemap['sections']:
        if section['title'][lang] == 'API':
            sections = section['sections']
            break

    if sections:
        sections.append({
            '$ref': {
                lang: '%s/%s' % (Content.DOCUMENTATION, _get_sitemap_name(lang, 'operators'))
            }
        })


def book_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    _book_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, 'en')
    _book_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, 'zh')


def models_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    _create_models_sitemap(generated_documentation_dir, version, 'README.html', output_dir_name, 'en')
    _create_models_sitemap(generated_documentation_dir, version, 'README.cn.html', output_dir_name, 'zh')


def _create_models_sitemap(generated_documentation_dir, version, html_file_name, output_dir_name, language):
    """
    Generate a sitemap for models' content by parsing the content of the index
    (root readme) file. Iterates through all the links inside list items of the
    file, and writes the constructed sitemap file.
    """
    github_path = 'https://github.com/PaddlePaddle/models/tree/'

    root_html_path = os.path.join(generated_documentation_dir, html_file_name)

    # Create models sitemap template
    sections = []

    title = '模型库' if language == 'zh' else 'Models'
    link = '%s/%s' % (Content.MODELS, html_file_name)

    sitemap = {
        'title': { language: title },
        'sections': [
            {
               'title': {language: title},
               'link': {language: link},
               'sections': sections
            }
        ]
    }

    # Read the stripped html file.
    # TODO [Jeff Wang]: Confirm the root_html_path is correct
    with open(root_html_path) as original_html_file:
        soup = BeautifulSoup(original_html_file, 'lxml')

        anchor_tags = soup.select('li a[href]')

        # Extract the links and the article titles
        for tag in anchor_tags:
            title = { language: tag.text }

            # The absolute URLs link to the github site.
            # Transform them into relative URL for local HTML files.
            # Dynamically remove develop or v0.10.0, etc
            # NOTE: Use of `link_zh` instead of `link` because all the links lead to Chinese pages.
            link_zh = Content.MODELS + '/' + tag['href']
            link = { language: link_zh }

            section = { 'title': title, 'link': link }
            sections.append(section)

    # TODO [Jeff Wang]: Confirm the models sitemap path is correct
    versioned_dest_dir = get_destination_documentation_dir(version, output_dir_name)
    if not os.path.isdir(versioned_dest_dir):
        os.makedirs(versioned_dest_dir)

    # Update the models' site.json by writing a new version.
    sitemap_path = get_sitemap_destination_path(versioned_dest_dir, language)
    with open(sitemap_path, 'w') as outfile:
        json.dump(sitemap, outfile)


def get_destination_documentation_dir(version, output_dir_name):
    return '%s/docs/%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, version, output_dir_name)


def get_sitemap_destination_path(versioned_dest_dir, lang, tag=None):
    return os.path.join(versioned_dest_dir, _get_sitemap_name(lang, tag))


def _get_sitemap_name(lang, tag=None):
    if tag:
        return 'site.%s.%s.json' % (tag, lang)
    else:
        return 'site.%s.json' % lang


def _book_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, lang):
    title = 'Book'
    root_json_path_template = '.tools/templates/index.html.json'
    sections_title = 'Deep Learning 101'

    if lang == 'zh':
        title = '深度学习101'
        root_json_path_template = '.tools/templates/index.cn.html.json'
        sections_title = '深度学习101'

    sections = []
    sitemap = { 'title': {lang: title}, 'sections': [{'title':{lang: sections_title}, 'sections':sections}]}

    # Read .tools/templates/index.html.json and .tools/templates/index.cn.html.json to generate the sitemap.
    root_json_path = os.path.join(original_documentation_dir, root_json_path_template)
    json_data = open(root_json_path).read()
    json_map = json.loads(json_data, object_pairs_hook=OrderedDict)

    # Go through each item and put it into the right format
    chapters = json_map['chapters']
    for chapter in chapters:
        parsed_section = {}

        if chapter['name']:
            parsed_section['title'] = {lang: chapter['name']}

        if chapter['link']:
            link = chapter['link']
            link = link.replace('./', '%s/' % Content.BOOK, 1)
            parsed_section['link'] = {lang: link}

        sections.append(parsed_section)

    versioned_dest_dir = get_destination_documentation_dir(version, output_dir_name)
    if not os.path.isdir(versioned_dest_dir):
        os.makedirs(versioned_dest_dir)

    # Output the json file
    sitemap_path = get_sitemap_destination_path(versioned_dest_dir, lang)
    with open(sitemap_path, 'w') as outfile:
        json.dump(sitemap, outfile)


def mobile_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    _mobile_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, 'en')
    _mobile_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, 'zh')


def _mobile_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, lang):
    title = 'Mobile'
    root_json_path_template = '/%s/README.html' % Content.MOBILE

    if lang == 'zh':
        title = '移动端'
        root_json_path_template = '/%s/README.cn.html' % Content.MOBILE

    root_section = {
        'title': {lang: title},
        'link': {lang: root_json_path_template}
    }

    sitemap = root_section.copy()

    sitemap['sections'] = [root_section]
    sub_section = []
    root_section['sections'] = sub_section

    root_html_path = os.path.join(generated_documentation_dir, 'README.html')
    with open(root_html_path) as original_html_file:
        anchor_tags = BeautifulSoup(original_html_file, 'lxml').select('li a[href]')

        # Extract the links and the article titles
        for tag in anchor_tags:
            title = {lang: tag.text}
            href = tag['href'].replace('./', '%s/' % Content.MOBILE, 1)
            link = {lang: href}
            section = {'title': title, 'link': link}
            sub_section.append(section)

    versioned_dest_dir = get_destination_documentation_dir(version, output_dir_name)
    if not os.path.isdir(versioned_dest_dir):
        os.makedirs(versioned_dest_dir)

    # Update the mobile site.json by writing a new version.
    sitemap_path = get_sitemap_destination_path(versioned_dest_dir, lang)
    with open(sitemap_path, 'w') as outfile:
        json.dump(sitemap, outfile)


def generate_operators_sitemap(versioned_dest_dir, lang):
    sitemap_ouput_path = get_sitemap_destination_path(versioned_dest_dir, lang, 'operators')
    sitemap = {
        'title': {
            # TODO(Jeff): Translate word to Chinese.
            lang: 'Operators' if lang == 'en' else 'Operators'
        },
        'link': {
            lang: '/documentation/%s/operators.html' % (lang)
        },
        'links': [
            '/documentation/%s/operators.html' % (lang)
        ]
    }

    with open(sitemap_ouput_path, 'w') as outfile:
        json.dump(sitemap, outfile)
