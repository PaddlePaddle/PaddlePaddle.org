# -*- coding: utf-8 -*-
import os
import re
import json
from collections import OrderedDict, Mapping
from django.conf import settings
from bs4 import BeautifulSoup


def sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    versioned_dest_dir = _get_destination_documentation_dir(version, output_dir_name)
    print 'GENERATING SITEMAP FOR PADDLE'

    parent_path_map = { 'en': '/en/html/',
                        'zh': '/cn/html/' }

    if version == '0.10.0' or version == '0.9.0':
        parent_path_map = { 'en': '/doc/',
                            'zh': '/doc_cn/'}

    for lang, parent_path in parent_path_map.items():
        index_html_path = '%s/%s/index.html' % (generated_documentation_dir, parent_path)

        sitemap = _create_sphinx_site_map_from_index(index_html_path, lang)
        sitemap_ouput_path = os.path.join(versioned_dest_dir, 'site.%s.json' % lang)

        with open(sitemap_ouput_path, 'w') as outfile:
            json.dump(sitemap, outfile)


def _create_sphinx_site_map_from_index(index_html_path, language):
    '''
    Creates Paddle doc TOC from HTML navigation.  Example of HTML:
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
    '''
    with open(index_html_path) as html:
        chapters = []

        sitemap = OrderedDict()
        sitemap['title'] = OrderedDict( { 'en': 'Documentation', 'zh': '文件'} )
        sitemap['sections'] = chapters

        navs = BeautifulSoup(html, 'lxml').findAll('nav', class_='doc-menu-vertical')

        if len(navs) > 0:
            chapters_container = navs[0].find('ul', recursive=False)
            if chapters_container:

                for chapter in chapters_container.find_all('li', recursive=False):
                    _create_sphinx_site_map(chapters, chapter, language)
        else:
            print 'Cannot generate sphinx sitemap, nav.doc-menu-vertical not found in %s' % index_html_path

        return sitemap


def _create_sphinx_site_map(parent_list, node, language):
    if node:
        node_dict = OrderedDict()
        if parent_list != None:
            parent_list.append(node_dict)

        first_link = node.find('a')
        if first_link:
            link_url = '/documentation/%s/%s' % (language, first_link['href'])
            node_dict['title'] = OrderedDict({ language: first_link.text })
            node_dict['link'] = OrderedDict({ language: link_url})

        sections = node.findAll('ul', recursive=False)
        for section in sections:
            sub_sections = section.findAll('li', recursive=False)

            if len(sub_sections) > 0:
                node_dict['sections'] = []

                for sub_section in sub_sections:
                    _create_sphinx_site_map(node_dict['sections'], sub_section, language)


def book_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    _book_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, 'en')
    _book_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, 'zh')


def models_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    _create_models_sitemap(generated_documentation_dir, version, 'README.html', output_dir_name, 'en')
    _create_models_sitemap(generated_documentation_dir, version, 'README.html', output_dir_name, 'zh')


def _create_models_sitemap(generated_documentation_dir, version, html_file_name, output_dir_name, language):
    github_path = 'https://github.com/PaddlePaddle/models/tree/'

    root_html_path = os.path.join(generated_documentation_dir, html_file_name)

    # Create models sitemap template
    sections = []

    title = '模型' if language == 'zh' else 'Models'
    link = 'models/%s' % html_file_name
    sitemap = { 'title': {language: title},
                'sections': [
                    {
                       'title': {language: title},
                       'link': {language: link},
                       'sections': sections
                    }
                ]
            }

    # Read the stripped html file
    # TODO [Jeff Wang]: Confirm the root_html_path is correct
    with open(root_html_path) as original_html_file:
        soup = BeautifulSoup(original_html_file, 'lxml')

        anchor_tags = soup.select('li a[href]')
        # Extract the links and the article titles
        for tag in anchor_tags:
            title = {language: tag.text}
            # The absolute URLs link to the github site. Transform them into relative URL for local HTML files.
            # dynamically remove develop or v0.10.0, etc
            link_zh = tag['href'].replace(github_path, '')
            link_zh = re.sub(r"^v?[0-9]+\.[0-9]+\.[0-9]+/|^develop/", 'models/', link_zh) + '/' + html_file_name

            link = {language: link_zh}

            section = {'title': title, 'link': link}
            sections.append(section)

    # TODO [Jeff Wang]: Confirm the models sitemap path is correct
    versioned_dest_dir = _get_destination_documentation_dir(version, output_dir_name)
    if not os.path.isdir(versioned_dest_dir):
        os.makedirs(versioned_dest_dir)
    sitemap_path = os.path.join(versioned_dest_dir, 'site.%s.json' % language)
    # Update the models.json
    with open(sitemap_path, 'w') as outfile:
        json.dump(sitemap, outfile)


def _get_destination_documentation_dir(version, output_dir_name):
    return '%s/docs/%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, version, output_dir_name)


def _book_sitemap_with_lang(original_documentation_dir, generated_documentation_dir, version, output_dir_name, lang):
    title = 'Book'
    root_json_path_template = '.tools/templates/index.html.json'
    output_file_name = 'site.en.json'
    sections_title = 'Deep Learning 101'

    if lang == 'zh':
        title = '专题文章'
        root_json_path_template = '.tools/templates/index.cn.html.json'
        output_file_name = 'site.zh.json'
        sections_title = '深度学习入门'

    sections = []
    sitemap = {"title": {lang: title}, 'sections': [{'title':{lang: sections_title}, 'sections':sections}]}

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
            link = link.replace('./', 'book/', 1)
            parsed_section['link'] = {lang: link}

        sections.append(parsed_section)

    versioned_dest_dir = _get_destination_documentation_dir(version, output_dir_name)
    if not os.path.isdir(versioned_dest_dir):
        os.makedirs(versioned_dest_dir)

    # Output the json file
    sitemap_path = os.path.join(versioned_dest_dir, output_file_name)
    with open(sitemap_path, 'w') as outfile:
        json.dump(sitemap, outfile)

