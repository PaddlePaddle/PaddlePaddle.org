import os
import json

from bs4 import BeautifulSoup

from portal import url_helper


def build_sphinx_index_from_menu(menu_path, lang):
    links = ['..  toctree::', '  :maxdepth: 1', '']

    # Generate an index.rst based on the menu.
    with open(menu_path, 'r') as menu_file:
        menu = json.loads(menu_file.read())
        links += _get_links_in_sections(menu['sections'], lang)

    # Manual hack because the documentation marks the language code differently.
    if lang == 'zh':
        lang = 'cn'

    with open(os.path.dirname(menu_path) + ('/index_%s.rst' % lang), 'w') as index_file:
        index_file.write('\n'.join(links))


def create_sphinx_menu(source_dir, content_id, lang, version, new_menu, generated_dir):
    with open(os.path.join(generated_dir, 'index_%s.html' % (
        'cn' if lang == 'zh' else 'en'))) as index_file:

        navs = BeautifulSoup(index_file, 'lxml').findAll(
            'nav', class_='doc-menu-vertical')

        assert navs > 0

        links_container = navs[0].find('ul', recursive=False)

        if links_container:
            for link in links_container.find_all('li', recursive=False):
                _build_menu_links(
                    new_menu['sections'], link, lang, version,
                    source_dir, content_id == 'docs'
                )


def remove_sphinx_menu(menu_path, lang):
    """Undoes the function above"""
    if lang == 'zh':
        lang = 'cn'

    os.remove(os.path.dirname(menu_path) + ('/index_%s.rst' % lang))


def _build_menu_links(parent_list, node, language, version, source_dir, allow_parent_links=True):
    """
    Recursive function to append links to a new parent list object by going down the
    nested lists inside the HTML, using BeautifulSoup tree parser.
    """
    if node:
        node_dict = {}
        if parent_list != None:
            parent_list.append(node_dict)

        sections = node.findAll('ul', recursive=False)

        first_link = node.find('a')
        if first_link:
            node_dict['title'] = { language: first_link.text }

            # If we allow parent links, then we will add the link to the parent no matter what
            # OR if parent links are not allowed, and the parent does not have children then add a link
            if allow_parent_links or not sections:
                alternative_urls = url_helper.get_alternative_file_paths(first_link['href'])

                if os.path.exists(os.path.join(source_dir, alternative_urls[0])):
                    node_dict['link'] = { language: alternative_urls[0] }
                else:
                    node_dict['link'] = { language: alternative_urls[1] }

        for section in sections:
            sub_sections = section.findAll('li', recursive=False)

            if len(sub_sections) > 0:
                node_dict['sections'] = []

                for sub_section in sub_sections:
                    _build_menu_links(
                        node_dict['sections'], sub_section,
                        language, version, source_dir, allow_parent_links)


def _get_links_in_sections(sections, lang):
    links = []

    for section in sections:
        if 'link' in section and lang in section['link']:
            links.append('  ' + section['link'][lang])

        if 'sections' in section:
            links += _get_links_in_sections(section['sections'], lang)

    return links
