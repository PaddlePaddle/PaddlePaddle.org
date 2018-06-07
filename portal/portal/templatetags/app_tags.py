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

from django import template
from portal import sitemap_helper
from portal import portal_helper
from django.conf import settings

from portal import url_helper

register = template.Library()


@register.assignment_tag(takes_context=False)
def get_dict_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag(takes_context=True)
def translation(context, leaf_node):
    """
    The leaf node of the sitemap.json could be a dictionary of a string
    When encountering a dictionary leaf node, load the value associated with the current language code
    """
    result = None

    if isinstance(leaf_node, basestring):
        result = leaf_node
    elif isinstance(leaf_node, dict):
        current_lang_code = context.request.LANGUAGE_CODE

        if current_lang_code in leaf_node:
            result = leaf_node[current_lang_code]

    return result


@register.assignment_tag(takes_context=True)
def translation_assignment(context, leaf_node):
    return translation(context, leaf_node)


@register.assignment_tag(takes_context=True)
def first_book_url_assignment(context, book, content_id):
    # Finds the first url in the book in the default category
    if book and 'default-category' in book:
        category = book['default-category']

        if content_id == portal_helper.Content.DOCUMENTATION or \
           content_id == portal_helper.Content.API:
            # For Documentation or API, we also filter by category
            api_category = context.get('CURRENT_API_VERSION', None)
            if api_category:
                category = api_category

        leaf_node = book['categories'][category]
        if ('link' in leaf_node):
            return translation(context, leaf_node['link'])

    return ''


@register.simple_tag(takes_context=True)
def apply_class_if_template(context, template_file_name, class_name):
    '''
    Function that returns 'active' if the current base template matches the passed in template name, otherwise return
    empty string.  This method is used to apply the "active" class to the root navigation links
    :param context:
    :param template_file_name:
    :return:
    '''
    if context.template.name == template_file_name:
        return class_name
    else:
        return ''


@register.inclusion_tag('_nav_bar.html', takes_context=True)
def nav_bar(context):
    """
    Build the navigation based on the current language.
    """
    current_lang_code = context.request.LANGUAGE_CODE

    root_navigation = sitemap_helper.get_top_level_navigation(
        portal_helper.get_preferred_version(context.request),
        current_lang_code
    )


    # TODO[thuan]: This is kinda hacky, need to find better way of removing visualdl docs from PPO
    if 'visualdl' in root_navigation:
        root_navigation.pop('visualdl')

    # NOTE: This is to consolidate all into documentation
    if 'book' in root_navigation:
        root_navigation.pop('book')

    if 'api' in root_navigation:
        root_navigation.pop('api')

    if 'mobile' in root_navigation:
        root_navigation.pop('mobile')

    if 'models' in root_navigation:
        root_navigation.pop('models')

    # Since we default to english, we set the change lang toggle to chinese
    lang_label = u'中文'
    lang_link = '/change-lang?lang_code=zh'
    community_link = 'https://github.com/PaddlePaddle/Paddle/issues'
    about_link = '/about_en.html'

    if current_lang_code and current_lang_code == 'zh':
        lang_label = 'English'
        lang_link = '/change-lang?lang_code=en'
        community_link = 'https://ai.baidu.com/forum/topic/list/168'
        about_link = '/about_cn.html'

    return _common_context(context, {
        'root_nav': root_navigation,
        'lang_def': { 'label': lang_label, 'link': lang_link },
        'community_link': community_link,
        'about_link': about_link
    })


@register.inclusion_tag('_content_links.html', takes_context=True)
def content_links(context, content_id):
    current_lang_code = context.request.LANGUAGE_CODE
    docs_version = context.get('CURRENT_DOCS_VERSION', None)

    #side_nav_content, category = sitemap_helper.get_content_navigation(
    side_nav_content = sitemap_helper.get_content_navigation(
        context.request,
        content_id,
        docs_version,
        current_lang_code
    )

    return _common_context(context, {
        'side_nav_content': side_nav_content,
        # 'category': category,
        'allow_search': context.get('allow_search', False),
        'allow_version': context.get('allow_version', False),
        'search_url': context.get('search_url', None)
    })


@register.inclusion_tag('_version_links.html', takes_context=True)
def version_links(context):
    # if content_id == portal_helper.Content.DOCUMENTATION or \
    #                 content_id == portal_helper.Content.API:
    #     # API section needs to be additonally filtered by API Version
    #     versions = _get_api_version_to_paddle_versions(content_id)
    # else:
    #     versions = [
    #         {
    #             "versions": sitemap_helper.get_available_versions(content_id)
    #         }
    #     ]

    # Make a copy because otherwise settings persist in the process.
    versions = list(settings.VERSIONS)
    versions.reverse()

    return _common_context(context, {
        'versions':versions,
    })


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


def _common_context(context, additional_context):
    if not additional_context:
        additional_context = {}

    additional_context.update({
        'request': context.request,
        'template': context.template,
        'url_helper': context.get('url_helper', None),
        'settings': context.get('settings', None),
        'content_id': context.get('content_id', ''),
        'CURRENT_DOCS_VERSION': context.get('CURRENT_DOCS_VERSION', ''),
        'CURRENT_API_VERSION': context.get('CURRENT_API_VERSION', '')
    })

    return additional_context
