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


def get_html_page_path(prefix, path):
    transformed_path = os.path.splitext(urlparse(path).path)[0] + '.html'
    return '/%s/%s' % (prefix, transformed_path)


def get_page_url_prefix(content_id, lang, version):
    return '%s/%s/%s' % (content_id, lang, version)
