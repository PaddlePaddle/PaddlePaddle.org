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

from django.conf import settings
from django.core.cache import cache

from portal import url_helper


def get_sitemap(version, language):
    """
    Given a version and language, fetch the sitemap for all contents from the
    cache, if available, or load them from the pre-compiled sitemap.
    """
    cache_key = 'sitemap.%s.%s' % (version, language)
    sitemap_cache = cache.get(cache_key, None)

    if not sitemap_cache:
        sitemap_cache = _load_sitemap_from_file(version, language)

        if sitemap_cache:
            cache.set(cache_key, sitemap_cache)
        else:
            raise Exception('Cannot generate sitemap for version %s' % version)

    return sitemap_cache


def _load_sitemap_from_file(version, language):
    """
    [For now] Returns a freshly generated sitemap file, given a version and language.
    """
    sitemap = None
    sitemap_path = _get_sitemap_path(version, language)

    if os.path.isfile(sitemap_path):
        # Sitemap file exists, lets load it
        try:
            with open(sitemap_path) as json_data:
                print 'Loading sitemap from %s' % sitemap_path
                sitemap = json.loads(json_data.read(), object_pairs_hook=collections.OrderedDict)
                cache.set(get_all_links_cache_key(version, language), sitemap['all_links_cache'], None)

        except Exception as e:
            print 'Cannot load sitemap from file %s: %s' % (sitemap_path, e.message)

    if not sitemap:
        # We couldn't load sitemap.<version>.json file, lets generate it
        sitemap = generate_sitemap(version, language)

    return sitemap


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

        for key, value in navigation.items():
            if key == '$ref' and language in value:
                # The value is the relative path to the associated json file
                referenced_json = load_json_and_resolve_references(value[language], version, language)
                resolved_navigation = referenced_json
            else:
                resolved_navigation[key] = _resolve_references(value, version, language)

        return resolved_navigation

    else:
        # leaf node: The type of navigation should be [string, int, float, unicode]
        return navigation


def _transform_sitemap_urls(version, sitemap, language):
    """
    Since paths defined in assets/sitemaps/<version>.json are defined relative to the folder structure of the content
    directories, we will need to append the URL path prefix so our URL router knows how to resolve the URLs.

    ex:
    /documentation/en/getstarted/index_en.html -> /docs/<version>/documentation/en/gettingstarted/index_en.html
    /book/01.fit_a_line/index.html -> /docs/<version>/book/01.fit_a_line/index.html

    :param version:
    :param sitemap:
    :return:
    """
    all_links_cache = {}
    if sitemap:
        for _, book in sitemap.items():
            _transform_urls(version, sitemap, book, all_links_cache, language)

    sitemap['all_links_cache'] = all_links_cache
    cache.set(get_all_links_cache_key(version, language), all_links_cache, None)


def _transform_urls(version, sitemap, node, all_links_cache, language):
    all_node_links = []

    if sitemap and node:
        if 'link' in node and language in node['link']:
            transformed_path = node['link'][language]

            if not transformed_path.startswith('http'):
                # We only append the document root/version if this is not an absolute URL
                path_with_prefix = url_helper.append_prefix_to_path(version, transformed_path)
                if path_with_prefix:
                    transformed_path = path_with_prefix

            if transformed_path:
                node['link'][language] = transformed_path

            all_node_links.append(transformed_path)

            if all_links_cache != None:
                key = url_helper.link_cache_key(transformed_path)
                all_links_cache[key] = transformed_path

        if 'sections' in node:
            for child_node in node['sections']:
                child_node_links = _transform_urls(version, sitemap, child_node, all_links_cache, language)
                all_node_links.extend(child_node_links)

        node['links'] = all_node_links
        if ('link' not in node or language not in node['link']):
            # After we process the node's children, we check if the node has a default link.
            # If not, then we set the node's first link
            if len(all_node_links) > 0:
                node['link'] = {
                    language: all_node_links[0]
                }

    return all_node_links


def get_content_navigation(content_id, version, language):
    """
    Get the navigation sitemap for a particular content service.
    """
    root_nav = get_sitemap(version, language)
    return root_nav.get(content_id, None)


def get_doc_subpath(version):
    return 'docs/%s/' % version


def _get_sitemap_path(version, language):
    """
    Get the sitemap path to the current version and language.
    """
    if not os.path.exists(settings.RESOLVED_SITEMAP_DIR):
        os.makedirs(settings.RESOLVED_SITEMAP_DIR)
        os.chmod(settings.RESOLVED_SITEMAP_DIR, 0775)

    return '%s/sitemap.%s.%s.json' % (settings.RESOLVED_SITEMAP_DIR, version, language)


def get_available_versions():
    """
    Go through all the generated folders inside the parent content directory's
    versioned `docs` dir, and return a list of the first-level of subdirectories.
    """
    versions = None
    path = '%s/docs' % settings.EXTERNAL_TEMPLATE_DIR
    for root, dirs, files in os.walk(path):
        if root == path:
            versions = dirs
            break

    # Divide versions into two catrgories
    # number based: EX: 0.1.0, 1.3.4
    # string based: EX: develop
    string_based_version = []
    number_based_version = []

    if versions:
        for version in versions:
            normalized_version = version.split('.')
            if len(normalized_version) > 1:
                number_based_version.append(version)
            else:
                string_based_version.append(version)

    # Sort both versions
    number_based_version.sort(key = lambda s: list(map(int, s.split('.'))))
    string_based_version.sort()

    return number_based_version + string_based_version


def get_all_links_cache_key(version, lang):
    return 'links.%s.%s' % (version, lang)


def get_external_file_path(sub_path):
    return '%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, sub_path)


def remove_all_resolved_sitemaps():
    try:
        if os.path.exists(settings.RESOLVED_SITEMAP_DIR):
            shutil.rmtree(settings.RESOLVED_SITEMAP_DIR)
    except os.error as e:
        print 'Cannot remove resolved sitemaps: %s' % e
