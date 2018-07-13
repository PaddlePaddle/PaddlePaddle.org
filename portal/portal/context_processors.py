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

from django.conf import settings

from portal import portal_helper
from portal import url_helper


def base_context(request):
    path = urlparse(request.path).path
    content_id, lang, version = url_helper.get_parts_from_url_path(
        path)

    if not version:
        version = portal_helper.get_preferred_version(request)

    return {
        'CURRENT_DOCS_VERSION': version,
        'settings': settings,
        'url_helper': url_helper
    }
