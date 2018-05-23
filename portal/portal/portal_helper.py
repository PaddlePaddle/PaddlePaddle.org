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
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.conf import settings
from portal import sitemap_helper


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


def get_preferred_version(request):
    """
    Observes the user's cookie to find the preferred documentation version.
    """
    preferred_version = request.COOKIES.get(settings.PREFERRED_VERSION_NAME, settings.DEFAULT_DOCS_VERSION)
    # if settings.CURRENT_PPO_MODE == settings.PPO_MODES.DOC_EDIT_MODE:
    #     # In document generation mode, we only allow for 'doc_test' version
    #     preferred_version = settings.DEFAULT_DOCS_VERSION

    return preferred_version


def set_preferred_version(response, preferred_version):
    """
    Sets the preferred documentation version in the user's cookie.
    """
    if preferred_version:
        if response:
            response.set_cookie(settings.PREFERRED_VERSION_NAME, preferred_version)


def get_preferred_api_version(request):
    return request.COOKIES.get(settings.PREFERRED_API_VERSION_NAME, None)


def set_preferred_api_version(response, preferred_api_version):
    """
    Sets the preferred document api version in the user's session.
    """
    if preferred_api_version and response:
        response.set_cookie(settings.PREFERRED_API_VERSION_NAME, preferred_api_version)


def get_preferred_language(request):
    """
    Observes the user's session, and consequently the cookies,
    to find the preferred documentation language.
    """
    preferred_lang = request.session.get(LANGUAGE_SESSION_KEY, None)
    if not preferred_lang:
        default_lang = 'en'

        if request.LANGUAGE_CODE == 'zh':
            default_lang = 'zh'
        preferred_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, default_lang)

    return preferred_lang


def set_preferred_language(request, response, lang):
    """
    Sets the preferred documentation version in the user's session AND cookie.
    """
    request.session[LANGUAGE_SESSION_KEY] = lang
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
    request.session.modified = True


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
