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
    return filter(lambda i: i['dir'] is not None, settings.TOP_LEVEL_NAVIGATION)


def get_sitemap(version, language, content_id):
    """
    Given a version and language, fetch the sitemap for all contents from the
    cache, if available, or load them from the pre-compiled sitemap.
    """
    cache_key = 'menu.%s.%s' % (version, language)
    sitemap_cache = cache.get(cache_key, None)

    if not sitemap_cache:
        sitemap_cache, sitemap_dir  = _load_sitemap_from_file(version, language, content_id)

        if sitemap_cache:
            cache.set(cache_key, sitemap_cache)
        else:
            raise Exception('Cannot generate sitemap for version %s' % version)

    return sitemap_cache, sitemap_dir


def _load_sitemap_from_file(version, language, content_id):
    """
    [For now] Returns a freshly generated sitemap file, given a version and language.
    """
    sitemap = None

    #sitemap_filename = ('sitemap.%s.json' % language)
    sitemap_filename = ('menu.json')
    sitemap_path = _get_sitemap_path(sitemap_filename, content_id)

    if not sitemap_path:
        raise Exception('Cannot find a sitemap file with the name %s in the directory for: %s' % (sitemap_filename, content_id))

    if os.path.isfile(sitemap_path):
        # Sitemap file exists, lets load it
        try:
            with open(sitemap_path) as json_data:
                print 'Loading sitemap from %s' % sitemap_path
                sitemap = json.loads(json_data.read())

                # sitemap = json.loads(json_data.read(), object_pairs_hook=collections.OrderedDict)
                # cache.set(get_all_links_cache_key(version, language), sitemap['all_links_cache'], None)

        except Exception as e:
            print 'Cannot load sitemap from file %s: %s' % (sitemap_path, e.message)

    # if not sitemap:
    #     # We couldn't load sitemap.<version>.json file, lets generate it
    #     sitemap = generate_sitemap(version, language)

    return sitemap, sitemap_path



def _transform_section_urls(section, prefix):
    # """
    # Since paths defined in assets/sitemaps/<version>.json are defined relative to the folder structure of the content
    # directories, we will need to append the URL path prefix so our URL router knows how to resolve the URLs.
    #
    # ex:
    # /documentation/en/getstarted/index_en.html -> /docs/<version>/documentation/en/gettingstarted/index_en.html
    # /book/01.fit_a_line/index.html -> /docs/<version>/book/01.fit_a_line/index.html
    # """
    # all_links_cache = {}

    # Make a copy that we shall mutate.

    new_transformed_sections = []
    for subsection in section['sections']:
        # if book and DEFAULT_BRANCH in book and version != 'doc_test':
        #     version = book[DEFAULT_BRANCH]
        new_subsection = {}

        for key, value in subsection.items():
            if key == 'link':
                new_subsection['link'] = {}

                for lang, lang_link in subsection['link'].items():
                    new_subsection['link'][lang] = url_helper.get_html_page_path(
                        prefix, lang_link)

            elif key == 'sections':
                new_subsection['sections'] = _transform_section_urls(
                    subsection, prefix)

            else:
                new_subsection[key] = value

            # for category_data in book['categories'].itervalues():
            #_transform_urls(version, sitemap, category_data, all_links_cache, language)

        new_transformed_sections.append(new_subsection)

    return new_transformed_sections
    # sitemap['all_links_cache'] = all_links_cache
    # cache.set(get_all_links_cache_key(version, language), all_links_cache, None)



def get_content_navigation(request, content_id, version, language):
    """
    Get the navigation sitemap for a particular content service.
    """
    # from portal import portal_helper

    # category_data = None
    navigation = {'sections': _transform_section_urls(
        get_sitemap(version, language, content_id)[0],
        url_helper.get_page_url_prefix(content_id, language, version)
    )}

    # book = root_nav.get(content_id, None)
    # Go through all links and give them relative paths from the root.

    return navigation

    # if book:
    #     category = book['default-category']
    #
    #     if content_id == portal_helper.Content.DOCUMENTATION or \
    #                     content_id == portal_helper.Content.API:
    #         # For Documentation or API, we also filter by category
    #         api_category = portal_helper.get_preferred_api_version(request)
    #         if api_category:
    #             category = api_category
    #
    #     category_data = book['categories'][category]
    #
    # return category_data, category

def get_all_navigation(request, version, language):
    """
    Get the navigation sitemap for all.
    NOTE: THIS IS A HACK FOR MLK
    """

    # We only care about the category in documentation.
    docs, category = get_content_navigation(request, "documentation", version, language)
    all_data = docs

    apis, category_placeholder = get_content_navigation(request, "api", version, language)

    # NOTE: API's section title is not "API", therefore, we have to add the root level instead.
    if apis:
        all_data['sections'] += [apis]

    # According to the spec, show book, models, and mobile to all possible version
    # EXCEPT fluid 0.14.0 zh version
    if category != "fluid" or version != "0.14.0" or language != "zh":
        book, category_placeholder = get_content_navigation(request, "book", version, language)

        if book and 'sections' in book:
            all_data['sections'] += book['sections']
            all_data['links'] += book['links']

        models, category_placeholder = get_content_navigation(request, "models", version, language)
        # Force first level travis in models
        if models and 'sections' in models and len(models['sections']) > 0 and 'sections' in models['sections'][0]:
            models['sections'][0].pop('sections', None)
            all_data['sections'] += models['sections']
            all_data['links'] += models['links']

        mobile, category_placeholder = get_content_navigation(request, "mobile", version, language)
        # Force first level travis in mobile
        if mobile and 'sections' in mobile and len(mobile['sections']) > 0 and 'sections' in mobile['sections'][0]:
            mobile['sections'][0].pop('sections', None)
            all_data['sections'] += mobile['sections']
            all_data['links'] += mobile['links']

    return  all_data, category




def _get_sitemap_path(sitemap_filename, content_id):
    """
    Get the sitemap path to the current version and language.
    """
    repo_path = find_in_top_level_navigation('/' + content_id)

    if os.path.exists(repo_path['dir']):
        # os.makedirs(settings.RESOLVED_SITEMAP_DIR)
        # os.chmod(settings.RESOLVED_SITEMAP_DIR, 0775)
        if content_id == 'api':
            sitemap_filename = 'api/' + sitemap_filename

        return _find_sitemap_in_repo(repo_path['dir'], sitemap_filename)

    raise Exception('Cannot find the directory for %s: %s' % (
        content_id, repo_path['dir']))

    #return '%s/sitemap.%s.%s.json' % (settings.RESOLVED_SITEMAP_DIR, version, language)


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
            # if content_id:
            #     folder_path = '%s/%s/%s' % (path, version, content_id)
            #     if not os.path.isdir(folder_path):
            #         # If content_id folder does not exists in versioned directory,
            #         # then don't add it to list of available versions
            #         continue

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

def is_version_greater_eq(v1, v2):
    f = lambda s: list(map(int, s.split('.')))
    if v1 == 'develop':
        return True

    try:
        return f(v1) >= f(v2)
    except:
        return False


def get_external_file_path(sub_path):
    #return '%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, sub_path)
    return os.path.join(settings.WORKSPACE_DIR, sub_path)


##################################################################


DEFAULT_BRANCH = 'default-branch'

def generate_sitemap(version, language):
    """
    Using a sitemap template, generated a full sitemap using individual content
    sitemaps.
    """
    sitemap = None
    sitemap_template_path = '%s/assets/sitemaps/sitemap_tmpl.json' % settings.PROJECT_ROOT

    try:
        # Read the sitemap template.
        with open(sitemap_template_path) as json_data:
            sitemap = json.loads(json_data.read(), object_pairs_hook=collections.OrderedDict)

            # Resolve JSON references with contents' individual sitemaps.
            sitemap = _resolve_references(sitemap, version, language)

            # Change URLs to represent accurate URL paths and not references to repo directory structures.
            _transform_sitemap_urls(version, sitemap, language)

            sitemap_path = _get_sitemap_path(version, language)

        # Write the built sitemaps to the main sitemap file the app reads.
        with open(sitemap_path, 'w') as fp:
            json.dump(sitemap, fp)
            # Enable the write permissions so the deploy_docs scripts can delete the sitemaps to force updates.
            os.chmod(sitemap_path, 0664)

    except Exception as e:
        print 'Cannot generate sitemap from %s: %s' % (sitemap_template_path, e.message)
        traceback.print_exc()

    return sitemap


# def _transform_urls(version, sitemap, node, all_links_cache, language):
#     all_node_links = []
#
#     if sitemap and node:
#         if 'link' in node and language in node['link']:
#             transformed_path = node['link'][language]
#
#             if not transformed_path.startswith('http'):
#                 # We only append the document root/version if this is not an absolute URL
#                 path_with_prefix = url_helper.append_prefix_to_path(version, transformed_path)
#                 if path_with_prefix:
#                     transformed_path = path_with_prefix
#
#             if transformed_path:
#                 node['link'][language] = transformed_path
#
#             all_node_links.append(transformed_path)
#
#             if all_links_cache != None:
#                 key = url_helper.link_cache_key(transformed_path)
#                 all_links_cache[key] = transformed_path
#
#         if 'sections' in node:
#             for child_node in node['sections']:
#                 child_node_links = _transform_urls(version, sitemap, child_node, all_links_cache, language)
#                 all_node_links.extend(child_node_links)
#
#         node['links'] = all_node_links
#         if ('link' not in node or language not in node['link']):
#             # After we process the node's children, we check if the node has a default link.
#             # If not, then we set the node's first link
#             if len(all_node_links) > 0:
#                 node['link'] = {
#                     language: all_node_links[0]
#                 }
#
#     return all_node_links


def load_json_and_resolve_references(path, version, language):
    """
    Loads any sitemap file (content root or site's root sitemap), and resolves
    references to generate a combined sitemap dictionary.
    """
    sitemap = None
    sitemap_path = '%s/docs/%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, version, path)

    try:
        with open(sitemap_path) as json_data:
            sitemap = json.loads(json_data.read(), object_pairs_hook=collections.OrderedDict)

        # Resolve any reference in inner sitemap files.
        sitemap = _resolve_references(sitemap, version, language)
    except Exception as e:
        print 'Cannot resolve sitemap from %s: %s' % (sitemap_path, e.message)

    return sitemap


def _resolve_references(navigation, version, language):
    """
    Iterates through an object (could be a dict, list, str, int, float, unicode, etc.)
    and if it finds a dict with `$ref`, resolves the reference by loading it from
    the respective JSON file.
    """
    if isinstance(navigation, list):
        # navigation is type list, resolved_navigation should also be type list
        resolved_navigation = []

        for item in navigation:
            resolved_navigation.append(_resolve_references(item, version, language))

        return resolved_navigation

    elif isinstance(navigation, dict):
        # navigation is type dict, resolved_navigation should also be type dict
        resolved_navigation = collections.OrderedDict()

        if DEFAULT_BRANCH in navigation and version != 'doc_test':
            version = navigation[DEFAULT_BRANCH]

        for key, value in navigation.items():
            if key == '$ref' and language in value:
                # The value is the relative path to the associated json file
                referenced_json = load_json_and_resolve_references(value[language], version, language)
                if referenced_json:
                    resolved_navigation = referenced_json
            else:
                resolved_navigation[key] = _resolve_references(value, version, language)

        return resolved_navigation

    else:
        # leaf node: The type of navigation should be [string, int, float, unicode]
        return navigation


def get_doc_subpath(version):
    return 'docs/%s/' % version


def get_all_links_cache_key(version, lang):
    return 'links.%s.%s' % (version, lang)


def remove_all_resolved_sitemaps():
    try:
        if os.path.exists(settings.RESOLVED_SITEMAP_DIR):
            shutil.rmtree(settings.RESOLVED_SITEMAP_DIR)
    except os.error as e:
        print 'Cannot remove resolved sitemaps: %s' % e
