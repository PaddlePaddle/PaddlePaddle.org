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

from django.conf import settings, urls

# Here is a little taxonomy to know before approaching this page.
# Given a file in the repo with the path: "getstarted/install_en.rst", the
# following terms describe its different transformations.
#
# 1. url_path: '/documentation/docs/en/0.11.0/getstarted/install_en.html'
# 2. url_prefix: 'documentation/docs/en/0.11.0'
# 3. content_path: '<workspace path on disk>/pages/documentation/docs/en/0.11.0'
# 4. file_path: 'getstarted/install_en.rst' or 'getstarted/install_en.md'
# 5. page_path: 'getstarted/install_en.html'


def get_raw_page_path_from_html(url_path):
    """Does the opposite of `get_url_path`"""
    url_path_pieces = url_path.strip('/').split('/')

    if len(url_path_pieces) > 4:
        return get_alternative_file_paths('/'.join(url_path_pieces[4:]))

    return None


def get_alternative_file_paths(page_path):
    extensionless_file_path, extension = os.path.splitext(page_path)
    return (
        extensionless_file_path + '.rst', extensionless_file_path + '.md')


def get_url_path(prefix, path):
    transformed_path = os.path.splitext(urlparse(path).path)[0] + '.html'
    return '/%s/%s' % (prefix, transformed_path)


def get_page_url_prefix(content_id, lang, version):
    return 'documentation/%s/%s/%s' % (content_id, lang, version)


def get_parts_from_url_path(url_path):
    url_path_pieces = url_path.strip('/').split('/')

    if len(url_path_pieces) > 4:
        return url_path_pieces[1], url_path_pieces[2], url_path_pieces[3]

    return url_path_pieces[0], None, None


def get_full_content_path(content_id, lang, version):
    """
    Given content_id, language, and version, return the local path of the
    location of the content.
    """
    # workspace_path = os.path.join(settings.BASE_DIR, settings.WORKSPACE_DIR)
    #
    # if not os.path.exists(workspace_path):
    #     os.makedirs(workspace_path)
    url_prefix = get_page_url_prefix(content_id, lang, version)
    return '%s/%s' % (settings.PAGES_DIR, url_prefix), url_prefix
