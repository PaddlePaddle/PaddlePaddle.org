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

from django.conf import settings

from portal import portal_helper
from portal import url_helper


def base_context(request):
    return {
        'CURRENT_DOCS_VERSION': portal_helper.get_preferred_version(request),
        'CURRENT_API_VERSION': portal_helper.get_preferred_api_version(request),
        'settings': settings,
        'url_helper': url_helper
    }
