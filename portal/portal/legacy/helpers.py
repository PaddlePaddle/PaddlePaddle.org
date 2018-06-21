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

import os
import tarfile

import requests

class Content:
    DOCUMENTATION = 'documentation'
    API = 'api'
    MODELS = 'models'
    BOOK = 'book'
    MOBILE = 'mobile'
    BLOG = 'blog'
    VISUALDL = 'visualdl'
    OTHER = 'other'

CONTENT_ID_TO_FOLDER_MAP = {
    Content.DOCUMENTATION: 'Paddle',
    Content.MODELS: 'models',
    Content.BOOK: 'book',
    Content.MOBILE: 'Mobile',
    Content.BLOG: 'blog',
    Content.VISUALDL: 'VisualDL'
}

# Invert the keys and value.  This assumes that the values are all unique
FOLDER_MAP_TO_CONTENT_ID = {v: k for k, v in CONTENT_ID_TO_FOLDER_MAP.iteritems()}

def get_available_doc_folder_names():
    folder_names = []

    root_path = '%s' % settings.CONTENT_DIR

    for item in os.listdir(root_path):
        if os.path.isdir(os.path.join(root_path, item)) and not item.startswith('.'):
            if item in CONTENT_ID_TO_FOLDER_MAP.values():
                # Only add folders that exists in our map
                folder_names.append(item)

    return folder_names


def folder_name_for_content_id(content_id):
    # TODO[Thuan]: Get this from configuration file
    return CONTENT_ID_TO_FOLDER_MAP.get(content_id, None)


def content_id_for_folder_name(folder_name):
    # TODO[Thuan]: Get this from configuration file
    return FOLDER_MAP_TO_CONTENT_ID.get(folder_name, None)


def has_downloaded_workspace_file():
    dest_file_path = '%s/%s' % (settings.CONTENT_DIR, settings.WORKSPACE_ZIP_FILE_NAME)
    return os.path.isfile(dest_file_path)


def download_and_extract_workspace():
    dest_file_path = '%s/%s' % (settings.CONTENT_DIR, settings.WORKSPACE_ZIP_FILE_NAME)

    if not os.path.isfile(dest_file_path):
        r = requests.get(settings.WORKSPACE_DOWNLOAD_URL, stream=True)
        with open(dest_file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

        tar = tarfile.open(dest_file_path)
        tar.extractall(settings.CONTENT_DIR)
        tar.close()

    # Regenerate sitemaps
    sitemap_helper.remove_all_resolved_sitemaps()
    sitemap_helper.generate_sitemap('develop', 'en')
    sitemap_helper.generate_sitemap('develop', 'zh')


def _get_api_version_to_paddle_versions(content_id):
    versions = sitemap_helper.get_available_versions(content_id)

    fluid_min_version = '0.12.0'
    v1v2_min_version = '0.9.0'  # TODO: Implement upper bounds for v1v2 once its deprecated

    api_version_to_paddle_version = [
        {
            'key': 'fluid',
            'title': 'Fluid',
            'versions': [v for v in versions if sitemap_helper.is_version_greater_eq(v, fluid_min_version)]
        },
        {
            'key': 'v2/v1',
            'title': 'V2/V1',
            'versions': [v for v in versions if sitemap_helper.is_version_greater_eq(v, v1v2_min_version)]
        }
    ]
    return api_version_to_paddle_version


####################### Sitemap ##############################


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


def is_version_greater_eq(v1, v2):
    f = lambda s: list(map(int, s.split('.')))
    if v1 == 'develop':
        return True

    try:
        return f(v1) >= f(v2)
    except:
        return False
