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
from urlparse import urlparse, parse_qs
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

from portal import menu_helper, portal_helper, url_helper
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
    menu_path = menu_helper.get_menu_path_cache(
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
                # We are switching to new language
                matching_link = menu_helper.find_all_languages_for_link(
                    path_to_seek,
                    old_lang, menu['sections'], lang
                )
                version = old_version

            else:
                # We are switching to new version
                new_menu_path = menu_helper.get_menu_path_cache(
                    content_id, old_lang, version)

                with open(new_menu_path, 'r') as new_menu_file:
                    new_menu = json.loads(new_menu_file.read())

                    # Try to find this link in the new menu path.
                    # NOTE: We account for the first and last '/'.
                    matching_link = menu_helper.find_link_in_sections(
                        new_menu['sections'], path_to_seek)
                lang = old_lang

    if matching_link:
        content_path, url_prefix = url_helper.get_full_content_path(
            content_id, lang, version)

        # Because READMEs get replaced by index.htmls, so we have to undo that.
        if content_id in ['book'] and old_lang != lang:
            matching_link = os.path.join(os.path.dirname(
                matching_link), 'index.%shtml' % ('' if lang == 'en' else 'cn.'))

        return redirect(url_helper.get_url_path(url_prefix, matching_link))

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
        menu_path = menu_helper.get_menu_path_cache(
            content_id, lang, version)
        content_path, url_prefix = url_helper.get_full_content_path(
            content_id, lang, version)

        # Generate new content.
        _generate_content(os.path.dirname(
            menu_path), content_path, content_id, lang, version)

        return redirect(path)

    except Exception as e:
        return HttpResponseServerError("Cannot reload docs: %s" % e)


def _redirect_first_link_in_contents(request, content_id, version=None, lang=None, is_raw=False):
    """
    Given a version and a content service, redirect to the first link in it's
    navigation.
    """
    if not lang:
        lang = portal_helper.get_preferred_language(request)

    # Get the directory paths on the filesystem, AND of the URL.
    content_path, url_prefix = url_helper.get_full_content_path(
        content_id, lang, version)

    # If the content doesn't exist yet, try generating it.
    navigation = None
    try:
        navigation, menu_path = menu_helper.get_menu(content_id, lang, version)
        assert os.path.exists(content_path)

    except Exception, e:
        if type(e) in [AssertionError, IOError]:
            if type(e) == IOError:
                menu_path = e[1]

            _generate_content(os.path.dirname(
                menu_path), content_path, content_id, lang, version)

            if not navigation:
                navigation, menu_path = menu_helper.get_menu(
                    content_id, lang, version)
        else:
            raise e

    try:
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

        return redirect(url_helper.get_url_path(url_prefix, path) + ('?raw=1' if is_raw else ''))

    except Exception as e:
        print e.message
        return redirect('/')


def _generate_content(source_dir, destination_dir, content_id, lang, version):
    # If this content has been generated yet, try generating it.
    if not os.path.exists(destination_dir):

        # Generate the directory.
        os.makedirs(destination_dir)

    transform(source_dir, destination_dir, content_id, version, lang)


def _get_first_link_in_contents(navigation, lang):
    """
    Given a content's menu, and a language choice, get the first available link.
    """
    # If there are sections in the root of the menu.
    first_chapter = None
    if navigation and 'sections' in navigation and len(navigation['sections']) > 0:
        # Gotta find the first chapter in current language.
        for section in navigation['sections']:
            if 'title' in section and lang in section['title']:
                first_chapter = section
                break

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


def get_menu(request):
    if not settings.DEBUG:
        return HttpResponseServerError(
            'You need to be in a local development environment to show the raw menu')

    path = urlparse(request.META.get('HTTP_REFERER')).path

    content_id, lang, version = url_helper.get_parts_from_url_path(
        path)

    navigation, menu_path = menu_helper.get_menu(
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
    menu_path = menu_helper.get_menu_path_cache(
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


def about_en(request):
    return render(request, 'about_en.html')


def about_cn(request):
    return render(request, 'about_cn.html')


def content_home(request, content_id):
    is_raw = request.GET.get('raw', None) == '1'
    content_id = urlparse(request.path).path[15:]

    if hasattr(request, 'urlconf') and request.urlconf == 'visualDL.urls':
        content_id = 'visualdl'
    elif content_id == '':
        content_id = 'docs'

    return _redirect_first_link_in_contents(
        request, content_id,
        'develop' if content_id == 'visualdl' else portal_helper.get_preferred_version(request),
        None, is_raw
    )


def content_sub_path(request, path=None):
    """
    This is the primary function that renders all static content (.html) pages.
    It builds the context and passes it to the only documentation template rendering template.
    """
    is_raw = request.GET.get('raw', None)
    static_content = _get_static_content_from_template(path)

    # Because this is the best metadata we have on if this is VDL or not.
    is_visualdl = hasattr(
        request, 'urlconf') and request.urlconf == 'visualDL.urls'

    if is_raw and is_raw == '1':
        response = HttpResponse(static_content, content_type="text/html")
        return response
    else:
        response = render(request, '%scontent_panel.html' % ('visualdl/' if is_visualdl else ''), {
            'static_content': static_content
        })
        return response
