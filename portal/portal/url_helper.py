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

from urlparse import urlparse
import os
import re

from django.conf import settings, urls
from django.core.urlresolvers import reverse


def get_raw_page_path_from_html(url_path):
    """Does the opposite of `get_html_page_path`"""
    url_path_pieces = url_path.strip('/').split('/')

    if len(url_path_pieces) > 3:
        html_path = '/'.join(url_path_pieces[3:-1])
        extensionless_file_name = os.path.splitext(
            urlparse(url_path_pieces[-1]).path)[0]
        return (
            '%s/%s' % (html_path, extensionless_file_name + '.rst'),
            '%s/%s' % (html_path, extensionless_file_name + '.md')
        )

    return None


def get_html_page_path(prefix, path):
    transformed_path = os.path.splitext(urlparse(path).path)[0] + '.html'
    return '/%s/%s' % (prefix, transformed_path)


def get_page_url_prefix(content_id, lang, version):
    return '%s/%s/%s' % (content_id, lang, version)


def get_parts_from_url_path(url_path):
    url_path_pieces = url_path.strip('/').split('/')

    if len(url_path_pieces) > 3:
        return url_path_pieces[0], url_path_pieces[1], url_path_pieces[2]

    return url_path_pieces[0], None, None


def get_full_content_path(content_id, lang, version):
    """
    Given content_id, language, and version, return the local path of the
    location of the content.
    """
    workspace_path = os.path.join(settings.BASE_DIR, settings.WORKSPACE_DIR)

    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)

    content_prefix = get_page_url_prefix(content_id, lang, version)

    return '%s/%s' % (workspace_path, content_prefix), content_prefix


###########################################


BLOG_ROOT = 'blog/'
BOOK_ROOT = 'book/'
DOCUMENTATION_ROOT = 'documentation/'
API_ROOT = 'api/'
MODEL_ROOT = 'models/'
MOBILE_ROOT = 'mobile/'
VISUALDL_ROOT = 'visualdl/'
GITHUB_ROOT = 'https://raw.githubusercontent.com'

URL_NAME_CONTENT_ROOT = 'content_root'
URL_NAME_CONTENT = 'content_path'
URL_NAME_BLOG_ROOT = 'blog_root'
URL_NAME_BOOK_ROOT = 'book_root'
URL_NAME_OTHER = 'other_path'


def append_prefix_to_path(version, path):
    """
    The path in the sitemap generated is relative to the location of the file
    in the repository it is fetched from. Based on the URL pattern of the
    organization of contents on the website (which is tied to how contents are
    transformed and stored after being pulled from repositories), these paths
    evolve. This function sets the path in the navigation for where the static
    content pages will get resolved.
    """
    url = None

    if path:
        path = path.strip('/')

        if path.startswith(GITHUB_ROOT):
            url_name = URL_NAME_OTHER
            sub_path = os.path.splitext(urlparse(path).path[1:])[0] + '.html'
        else:
            url_name = URL_NAME_CONTENT
            sub_path = path

        url = reverse(url_name, args=[version, sub_path])
        # reverse method escapes #, which breaks when we try to find it in the file system.  We unescape it here
        url = url.replace('%23', '#')

    return url


def link_cache_key(path):
    # Remove all language specific strings
    key = re.sub(r'[._]?(en|cn|zh)?\.htm[l]?$', '', path)
    key = key.replace('/en/', '/')
    key = key.replace('/zh/', '/')

    return key
