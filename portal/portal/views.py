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

import os
import posixpath
import urllib
from urlparse import urlparse
import json

from django.template.loader import get_template
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils.six.moves.urllib.parse import unquote
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.views import static
from django.template import TemplateDoesNotExist
from django.core.cache import cache
from django.http import JsonResponse
from django import forms

from portal import sitemap_helper, portal_helper, url_helper
from deploy import transform
from portal import url_helper


def change_version(request):
    """
    Change current documentation version.
    """
    # Look for a new version in the URL get params.
    version = request.GET.get('preferred_version', settings.DEFAULT_DOCS_VERSION)

    response = redirect('/')

    path = urlparse(request.META.get('HTTP_REFERER')).path

    if not path == '/':
        response = _find_matching_equivalent_page_for(path, request, None, version)

    portal_helper.set_preferred_version(response, version)

    return response


def change_lang(request):
    """
    Change current documentation language.
    """
    lang = request.GET.get('lang_code', 'en')

    # By default, intend to redirect to the home page.
    response = redirect('/')

    path = urlparse(request.META.get('HTTP_REFERER')).path

    if not path == '/':
        response = _find_matching_equivalent_page_for(path, request, lang)

    portal_helper.set_preferred_language(request, response, lang)

    return response


def _find_matching_equivalent_page_for(path, request, lang=None, version=None):
    content_id, old_lang, old_version = url_helper.get_parts_from_url_path(
        path)

    # Try to find the page in this content's navigation.
    menu_path = sitemap_helper.get_menu_path_cache(
        content_id, old_lang, old_version)

    if content_id in ['book']:
        path = os.path.join(os.path.dirname(
            path), 'README.%smd' % ('' if old_lang == 'en' else 'cn.'))

    matching_link = None
    if menu_path.endswith('.json'):
        with open(menu_path, 'r') as menu_file:
            menu = json.loads(menu_file.read())
            path_to_seek = url_helper.get_raw_page_path_from_html(path)

            if lang:
                matching_link = sitemap_helper.find_all_languages_for_link(
                    path_to_seek,
                    old_lang, menu['sections'], lang
                )
                version = old_version

            else:
                path_prefix = url_helper.get_page_url_prefix(
                    content_id, old_lang, old_version)

                # Try to find this link in the menu path.
                # NOTE: We account for the first and last '/'.
                matching_link = sitemap_helper.find_link_in_sections(
                    menu['sections'], path_to_seek)
                lang = old_lang

    if matching_link:
        content_path, content_prefix = url_helper.get_full_content_path(
            content_id, lang, version)

        # Because READMEs get replaced by index.htmls, so we have to undo that.
        if content_id in ['book'] and old_lang != lang:
            matching_link = os.path.join(os.path.dirname(
                matching_link), 'index.%shtml' % ('' if lang == 'en' else 'cn.'))

        return redirect((url_helper.get_html_page_path(content_prefix, matching_link)))

    # If no such page is found, redirect to first link in the content.
    else:
        return _redirect_first_link_in_contents(
            request, content_id, version, lang)


def reload_docs(request):
    try:
        path = urlparse(request.META.get('HTTP_REFERER')).path

        # Get all the params from the URL and settings to generate new content.
        content_id, lang, version = url_helper.get_parts_from_url_path(
            path)
        menu_path = sitemap_helper.get_menu_path_cache(
            content_id, lang, version)
        content_path, content_prefix = url_helper.get_full_content_path(
            content_id, lang, version)

        # Generate new content.
        _generate_content(os.path.dirname(
            menu_path), content_path, content_id, lang, version)

        return redirect(path)

    except Exception as e:
        return HttpResponseServerError("Cannot reload docs: %s" % e)


def _redirect_first_link_in_contents(request, content_id, version=None, lang=None):
    """
    Given a version and a content service, redirect to the first link in it's
    navigation.
    """
    if not lang:
        lang = portal_helper.get_preferred_language(request)

    navigation, menu_path = sitemap_helper.get_sitemap(
        content_id, lang, version)

    try:
        # Get the directory paths on the filesystem, AND of the URL.
        content_path, content_prefix = url_helper.get_full_content_path(
            content_id, lang, version)

        # If the content doesn't exist yet, try generating it.
        if not os.path.exists(content_path):
            _generate_content(os.path.dirname(
                menu_path), content_path, content_id, lang, version)

        if navigation:
            path = _get_first_link_in_contents(navigation, lang)
        else:
            path = 'README.cn.html' if lang == 'zh' else 'README.html'

        # Because READMEs get replaced by index.htmls, so we have to undo that.
        if content_id in ['book']:
            path = os.path.join(os.path.dirname(path), 'index.%shtml' % (
                '' if lang == 'en' else 'cn.'))

        if not path:
            msg = 'Cannot perform reverse lookup on link: %s' % path
            raise Exception(msg)

        return redirect(url_helper.get_html_page_path(content_prefix, path))

    except Exception as e:
        print e.message
        return redirect('/')


def _generate_content(source_dir, destination_dir, content_id, lang, version):
    # If this content has been generated yet, try generating it.
    if not os.path.exists(destination_dir):

        # Generate the directory.
        os.makedirs(destination_dir)

    transform(content_id, source_dir, destination_dir, lang)


def _get_first_link_in_contents(navigation, lang):
    """
    Given a content's sitemap, and a language choice, get the first available link.
    """
    # If there are sections in the root of the sitemap.
    first_chapter = None
    if navigation and 'sections' in navigation and len(navigation['sections']) > 0:
        first_chapter = navigation['sections'][0]

    # If there is a known root "section" with links.
    if first_chapter and 'link' in first_chapter:
        return first_chapter['link'][lang]

    # Or if there is a known root section with subsections with links.
    elif first_chapter and ('sections' in first_chapter) and len(first_chapter['sections']) > 0:
        first_section = first_chapter['sections'][0]
        return first_section['link'][lang]

    # Last option is to attempt to see if there is only one link on the title level.
    elif 'link' in navigation:
        return navigation['link'][lang]


def static_file_handler(request, path, extension, insecure=False, **kwargs):
    """
    Note: This is static handler is only used during development.
    In production, the Docker image uses NGINX to serve static content.

    Serve static files below a given point in the directory structure or
    from locations inferred from the staticfiles finders.
    To use, put a URL pattern such as::
        from django.contrib.staticfiles import views
        url(r'^(?P<path>.*)$', views.serve)
    in your URLconf.
    It uses the django.views.static.serve() view to serve the found files.
    """
    append_path = ''

    if not settings.DEBUG and not insecure:
        raise Http404

    normalized_path = posixpath.normpath(unquote(path)).lstrip('/')

    absolute_path = settings.WORKSPACE_DIR + '/' + append_path + normalized_path + '.' + extension
    if not absolute_path:
        if path.endswith('/') or path == '':
            raise Http404('Directory indexes are not allowed here.')

        raise Http404('\'%s\' could not be found' % path)

    document_root, path = os.path.split(absolute_path)
    return static.serve(request, path, document_root=document_root, **kwargs)


def _render_static_content(request, path, content_id, additional_context=None):
    """
    This is the primary function that renders all static content (.html) pages.
    It builds the context and passes it to the only documentation template rendering template.
    """
    is_raw = request.GET.get('raw', None)
    static_content = _get_static_content_from_template(path)

    if is_raw and is_raw == '1':
        response = HttpResponse(static_content, content_type="text/html")
        return response
    else:
        context = {
            'static_content': static_content,
            'content_id': content_id,
        }

        if additional_context:
            context.update(additional_context)

        template = 'content_panel.html'
        if content_id in ['mobile', 'models']:
            template = 'content_doc.html'

        response = render(request, template, context)
        return response


def get_menu(request):
    if not settings.DEBUG:
        return HttpResponseServerError(
            'You need to be in a local development environment to show the raw menu')

    path = urlparse(request.META.get('HTTP_REFERER')).path

    content_id, lang, version = url_helper.get_parts_from_url_path(
        path)

    navigation, menu_path = sitemap_helper.get_sitemap(
        content_id, lang, version)

    return HttpResponse(json.dumps(navigation), content_type='application/json')


def save_menu(request):
    try:
        assert settings.DEBUG
        menu = json.loads(request.POST.get('menu'), None)
    except:
        return HttpResponseServerError('You didn\'t submit a valid menu')

    # Write the new menu to disk.
    path = urlparse(request.META.get('HTTP_REFERER')).path

    content_id, lang, version = url_helper.get_parts_from_url_path(
        path)
    menu_path = sitemap_helper.get_menu_path_cache(
        content_id, lang, version)

    with open(menu_path, 'w') as menu_file:
        menu_file.write(json.dumps(menu, indent=4))

    return HttpResponse(status='200')


######## Paths and content roots below ########################

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


def home_root(request):
    return render(request, 'index.html')


def zh_home_root(request):
    response = redirect('/')
    portal_helper.set_preferred_language(request, response, 'zh')
    return response


def content_home(request):
    path = request.path[1:]

    if '/' in path:
        path = path[0, path.index('/')]

    if '?' in path:
        path = path[0, path.index('?')]

    return _redirect_first_link_in_contents(
        request, path, portal_helper.get_preferred_version(request))


def content_sub_path(request, path=None):
    content_id = ''
    additional_context = {}

    content_id, lang, version = url_helper.get_parts_from_url_path(
        request.path)

    if content_id == 'documentation':
        lang = portal_helper.get_preferred_language(request)

        search_url = '%s/%s/search.html' % (content_id, lang)
        # if path.startswith(url_helper.DOCUMENTATION_ROOT + 'fluid'):
        #     search_url = '%s/fluid/%s/search.html' % (content_id, lang)

        additional_context = { 'allow_search': True, 'allow_version': True, 'search_url': search_url }

    elif content_id == 'api':
        search_url = '%s/%s/search.html' % (content_id, 'en')
        # if path.startswith(url_helper.API_ROOT + 'fluid'):
        #     search_url = '%s/fluid/%s/search.html' % (content_id, 'en')

        additional_context = {'allow_search': True, 'allow_version': True, 'search_url': search_url}

    return _render_static_content(request, path, content_id, additional_context)
