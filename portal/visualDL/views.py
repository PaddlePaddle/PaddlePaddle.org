# -*- coding: utf-8 -*-
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

import urllib

from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.shortcuts import render, redirect
from portal import portal_helper
from portal import menu_helper


def home_root(request):
    return render(request, 'visualdl/index.html')


def change_lang(request):
    """
    Change current documentation language.
    """
    lang = request.GET.get('lang_code', 'en')

    response = redirect('/')
    portal_helper.set_preferred_language(request, response, lang)

    return response
