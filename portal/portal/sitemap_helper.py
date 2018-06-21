#   Copyright (c) 2018 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import collections
import traceback
import shutil
from urlparse import urlparse

from django.conf import settings
from django.core.cache import cache

from portal import url_helper


def find_all_languages_for_link(possible_links, current_lang, sections, desired_lang):
    for section in sections:
        if 'link' in section and current_lang in section['link']:
            if (section['link'][current_lang] == possible_links[0] or (
                section['link'][current_lang] == possible_links[1])) and desired_lang in section['link']:
                return section['link'][desired_lang]

        if 'sections' in section:
            return find_all_languages_for_link(
                possible_links, current_lang, section['sections'], desired_lang)

    return None


def find_link_in_sections(sections, possible_links):
    for section in sections:
        if 'link' in section:
            for lang, lang_link in section['link'].items():
                if lang_link == possible_links[0] or lang_link == possible_links[1]:
                    return lang_link

        if 'sections' in section:
            lang_link = find_link_in_sections(section['sections'], possible_links)
            if lang_link:
                return lang_link


def set_menu_path_cache(content_id, lang, version, path):
    cache.set(
        '%s/%s' % ('menu_path', url_helper.get_page_url_prefix(
            content_id, lang, version)),
        path
    )


def get_menu_path_cache(content_id, lang, version):
    menu_path = cache.get(
        '%s/%s' % ('menu_path', url_helper.get_page_url_prefix(
            content_id, lang, version)),
        None
    )

    if not menu_path:
        menu_path = get_sitemap(version, lang, content_id)[1]
        set_menu_path_cache(content_id, lang, version, menu_path)

    return menu_path


def get_production_menu_path(content_id, lang, version):
    return os.path.join(settings.MENUS_DIR, '%s/%s/%s/menu.json' % (content_id, lang, version))


def find_in_top_level_navigation(path):
    for i in settings.TOP_LEVEL_NAVIGATION:
        if i['path'] == path:
            return i


def _find_sitemap_in_repo(path, filename):
    import fnmatch

    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(map(
            lambda x: root + '/' + x, filenames), '*' + filename):
            return filename

    return None


def get_top_level_navigation(version, language):
    """
    Returns a list of categories available for this version & language.
    """
    if settings.ENV in ['production', 'staging']:
        return [i for i in settings.TOP_LEVEL_NAVIGATION if os.path.exists(
            get_production_menu_path(i['path'][1:], language, version)
        )]

    return filter(lambda i: i['dir'] is not None, settings.TOP_LEVEL_NAVIGATION)


def get_sitemap(content_id, lang, version):
    """
    Given a version and language, fetch the sitemap for all contents from the
    cache, if available, or load them from the pre-compiled sitemap.

    [For now] Returns a freshly generated sitemap file, given a version and language.
    """
    # cache_key = 'menu.%s.%s' % (version, language)
    # sitemap_cache = cache.get(cache_key, None)

    # if sitemap_cache:
    #     cache.set(cache_key, sitemap_cache)
    # else:
    #     raise Exception('Cannot generate sitemap for version %s' % version)

    sitemap = None

    # These are the repos without menus.
    if content_id in ['models', 'mobile']:
        # NOTE(varunarora): This is a hack because there is no menu.json here.
        sitemap_path = None if settings.ENV in ['production', 'staging'] else _get_sitemap_path('', content_id)

    else:
        if settings.ENV in ['production', 'staging']:
            sitemap_path = get_production_menu_path(content_id, lang, version)
        else:
            sitemap_path = _get_sitemap_path('menu.json', content_id)

        if not sitemap_path:
            raise Exception('Cannot find a sitemap file with the name %s in the directory for: %s' % (sitemap_path, content_id))

        if os.path.isfile(sitemap_path):
            set_menu_path_cache(content_id, lang, version, sitemap_path)

            # Sitemap file exists, lets load it
            try:
                with open(sitemap_path) as json_data:
                    sitemap = json.loads(json_data.read())

                    # cache.set(get_all_links_cache_key(version, language), sitemap['all_links_cache'], None)

            except Exception as e:
                print 'Cannot load sitemap from file %s: %s' % (sitemap_path, e.message)

    return sitemap, sitemap_path


def _transform_section_urls(section, prefix, content_id):
    """
    Since paths defined in assets/sitemaps/<version>.json are defined relative to the folder structure of the content
    directories, we will need to append the URL path prefix so our URL router knows how to resolve the URLs.
    """
    # Make a copy that we shall mutate.
    new_transformed_sections = []
    for subsection in section['sections']:
        new_subsection = {}

        for key, value in subsection.items():
            if key == 'link':
                new_subsection['link'] = {}

                for lang, lang_link in subsection['link'].items():
                    if content_id in ['book']:
                        lang_link = os.path.join(os.path.dirname(lang_link), 'index.%shtml' % (
                            '' if lang == 'en' else 'cn.'))

                    new_subsection['link'][lang] = url_helper.get_html_page_path(
                        prefix, lang_link)

            elif key == 'sections':
                new_subsection['sections'] = _transform_section_urls(
                    subsection, prefix, content_id)

            else:
                new_subsection[key] = value

        new_transformed_sections.append(new_subsection)

    return new_transformed_sections


def get_content_navigation(request, content_id, language, version):
    """
    Get the navigation sitemap for a particular content service.
    """
    navigation = {'sections': _transform_section_urls(
        get_sitemap(content_id, language, version)[0],
        url_helper.get_page_url_prefix(content_id, language, version),
        content_id
    )}

    return navigation


def _get_sitemap_path(sitemap_filename, content_id):
    """
    Get the sitemap path to the current version and language.
    """
    repo_path = find_in_top_level_navigation('/' + content_id)

    if os.path.exists(repo_path['dir']):
        if content_id == 'api':
            sitemap_filename = 'api/' + sitemap_filename

        return _find_sitemap_in_repo(repo_path['dir'], sitemap_filename)

    raise Exception('Cannot find the directory for %s: %s' % (
        content_id, repo_path['dir']))


def get_available_versions(content_id=None):
    """
    Go through all the generated folders inside the parent content directory's
    versioned `docs` dir, and return a list of the first-level of subdirectories.
    """
    versions = None
    #path = '%s/docs' % settings.EXTERNAL_TEMPLATE_DIR
    path = os.path.join(settings.WORKSPACE_DIR, content_id)

    for root, dirs, files in os.walk(path):
        if root == path:
            versions = dirs
            break

    # Divide versions into two catrgories
    # number based: EX: 0.1.0, 1.3.4
    # string based: EX: develop
    # string_based_version = []
    number_based_version = []

    if versions:
        for version in versions:
            normalized_version = version.split('.')
            if len(normalized_version) > 1:
                number_based_version.append(version)
            # else:
            #     string_based_version.append(version)

    # Sort both versions, make sure the latest version is at the top of the list
    number_based_version.sort(key = lambda s: list(map(int, s.split('.'))),
                              reverse=True)
    # string_based_version.sort()

    # Note: Hide 'develop' version for now.
    # return string_based_version + number_based_version
    return number_based_version

def get_external_file_path(sub_path):
    return os.path.join(settings.WORKSPACE_DIR, sub_path)
