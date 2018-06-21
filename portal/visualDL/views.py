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
    return render(request, 'visualdl/index.html', _common_context(request))


def change_lang(request):
    """
    Change current documentation language.
    """
    lang = request.GET.get('lang_code', 'en')

    response = redirect('/')
    portal_helper.set_preferred_language(request, response, lang)

    return response


def content_sub_path(request, version, path=None):
    return _render_static_content(request, version, portal_helper.Content.VISUALDL,  _common_context(request))


def _common_context(request):
    current_lang_code = request.LANGUAGE_CODE

    # Since we default to english, we set the change lang toggle to chinese
    lang_label = u'中文'
    lang_link = '/change-lang?lang_code=zh'

    if current_lang_code and current_lang_code == 'zh':
        lang_label = 'English'
        lang_link = '/change-lang?lang_code=en'

    root_navigation = menu_helper.get_menu(
        'develop',
        current_lang_code
    )

    return {
        'lang_def': { 'label': lang_label, 'link': lang_link },
        'root_nav': root_navigation
    }


def _render_static_content(request, version, content_id, additional_context=None):
    """
    This is the primary function that renders all static content (.html) pages.
    It builds the context and passes it to the only documentation template rendering template.
    """

    static_content_path = menu_helper.get_external_file_path(request.path)

    context = {
        'static_content': _get_static_content_from_template(static_content_path),
        'content_id': content_id,
    }

    if additional_context:
        context.update(additional_context)

    template = 'visualdl/content_panel.html'

    response = render(request, template, context)
    if version:
        portal_helper.set_preferred_version(response, version)

    return response


def _get_static_content_from_template(path):
    """
    Search the path and render the content
    Return "Page not found" if the template is missing.
    """
    try:
        static_content_template = get_template(path)
        return static_content_template.render()

    except TemplateDoesNotExist:
        return 'Page not found: %s' % path
