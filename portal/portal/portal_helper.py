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

from django.utils.translation import LANGUAGE_SESSION_KEY
from django.conf import settings
from portal import menu_helper


def get_preferred_version(request):
    """
    Returns default docs version.
    """
    return settings.DEFAULT_DOCS_VERSION


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

        preferred_lang = request.COOKIES.get(
            settings.LANGUAGE_COOKIE_NAME, default_lang)

    return preferred_lang


def set_preferred_language(request, response, lang):
    """
    Sets the preferred documentation version in the user's session AND cookie.
    """
    request.session[LANGUAGE_SESSION_KEY] = lang
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
    request.session.modified = True
