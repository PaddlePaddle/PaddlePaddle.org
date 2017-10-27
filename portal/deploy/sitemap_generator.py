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
        soup = BeautifulSoup(html, 'lxml')

        navs = soup.findAll('nav', class_='doc-menu-vertical')

        if len(navs) > 0:
            toc_lis = navs[0].findAll('li', { 'class': re.compile('^toctree-.*$') })
            _create_sphinx_site_map(chapters, 0, 1, toc_lis, language)
        else:
            print 'Cannot generate sphinx sitemap, nav.doc-menu-vertical not found in %s' % index_html_path

        return sitemap


def _create_sphinx_site_map(parent_list, iterator_idx, level, li_elements, language):
    previous_child_node = None

    idx = iterator_idx
    while idx < len(li_elements):
        li = li_elements[idx]
        li_level = _get_toc_level(li['class'])

        all_anchors = li.findAll('a')

        if len(all_anchors) > 0:
            first_anchor = all_anchors[0]

            if li_level == -1:
                raise Exception('Invalid TOC level for li %s' % li)

            if li_level == level:
                if '#' not in first_anchor['href']:
                    # Do not include links that contains anchor references
                    child_node_dict = OrderedDict()
                    previous_child_node = child_node_dict
                    parent_list.append(child_node_dict)
                    link_url = '/documentation/%s/%s' % (language, first_anchor['href'])
                    child_node_dict['title'] = OrderedDict({ language: first_anchor.text})
                    child_node_dict['link'] = OrderedDict({ language: link_url})

            elif li_level > level:
                # This is a child level, lets recursively process it
                if previous_child_node:
                    sub_child_list = []
                    previous_child_node['sections'] = sub_child_list
                    idx = _create_sphinx_site_map(sub_child_list, idx, li_level, li_elements, language)
                else:
                    print 'Unhandled... li_level < level'

            elif li_level < level:
                # We went up a level, lets process this line again after we return from _create_sphinx_site_map
                return idx-1

        idx += 1

    return idx

def _get_toc_level(toc_classes):
    level = -1
    prefix = 'toctree-l'

    for toc_class_name in toc_classes:
        if toc_class_name and toc_class_name.startswith(prefix):
            level_str = toc_class_name[len(prefix):]
            level = int(level_str)
            break

    return level


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

