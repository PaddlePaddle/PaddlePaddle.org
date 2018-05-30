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
from deploy.documentation import transform, fetch_and_transform
from deploy.sitemap_generator import get_destination_documentation_dir, generate_operators_sitemap
from deploy.operators import generate_operators_page
from portal import url_helper
from portal_helper import Content


def change_version(request):
    """
    Change current documentation version.
    """
    # Look for a new version in the URL get params.
    preferred_version = request.GET.get('preferred_version', settings.DEFAULT_DOCS_VERSION)
    api_version = request.GET.get('api_version', None)

    # Refers to the name of the contents service, for eg. 'models', 'documentation', or 'book'.
    content_id = request.GET.get('content_id', None)

    # Infer language based on session/cookie.
    lang = portal_helper.get_preferred_language(request)

    root_navigation = sitemap_helper.get_sitemap(preferred_version, lang)

    response = home_root(request)

    if content_id:
        if content_id in root_navigation and root_navigation[content_id]:
            response = _redirect_first_link_in_contents(request, preferred_version, content_id, api_version)
        else:
            # This version doesn't support this book. Redirect it back to home
            response = redirect('/')

    # If no content service specified, just redirect to first page of root site navigation.
    elif root_navigation and len(root_navigation) > 0:
        for content_id, content in root_navigation.items():
            if content:
                response = _redirect_first_link_in_contents(request, preferred_version, content_id, api_version)

    portal_helper.set_preferred_version(response, preferred_version)
    portal_helper.set_preferred_api_version(response, api_version)

    return response


def change_lang(request):
    """
    Change current documentation language.
    """
    lang = request.GET.get('lang_code', 'en')

    # By default, intend to redirect to the home page.
    response = redirect('/')

    # Needs to set the preferred language first in case the following code reads lang from portal_helper.
    portal_helper.set_preferred_language(request, response, lang)

    # Use the page the user was on, right before attempting to change the language.
    # If there is a known page the user was on, attempt to redirect to it's root contents.
    from_path = urllib.unquote(request.GET.get('path', None))

    if from_path:
        # Get which content the user was reading.
        content_id = request.GET.get('content_id')

        if content_id:
            # Get the proper version.
            docs_version = portal_helper.get_preferred_version(request)

            # Grabbing root_navigation to check if the current lang supports this book
            # It also makes sure that all_links_cache is ready.
            root_navigation = sitemap_helper.get_sitemap(docs_version, lang)

            if content_id in root_navigation:
                all_links_cache = cache.get(sitemap_helper.get_all_links_cache_key(docs_version, lang), None)

                key = url_helper.link_cache_key(from_path)

                if all_links_cache and key in all_links_cache:
                    response = redirect(all_links_cache[key])
                else:
                    # There is no translated path. Use the first link in the contents instead
                    response = _redirect_first_link_in_contents(request, docs_version, content_id)

        # If the user happens to be coming from the blog.
        elif from_path.startswith('/blog'):
            # Blog doesn't a content_id and translated version. Simply redirect back to the original path.
            response = redirect(from_path)

    portal_helper.set_preferred_language(request, response, lang)

    return response


def reload_docs(request):
    try:
        if settings.CURRENT_PPO_MODE != settings.PPO_MODES.DOC_EDIT_MODE:
            raise Exception("Can only reload docs in DOCS_MODE")

        folder_name = request.GET.get('folder_name', None)
        build_type = request.GET.get('build_type', None)

        options = None
        if build_type:
            options = { 'build_type': build_type }

        if folder_name:
            content_id = portal_helper.content_id_for_folder_name(folder_name)
        else:
            content_id = request.GET.get('content_id', None)
            if content_id:
                folder_name = portal_helper.folder_name_for_content_id(content_id)

        if not folder_name:
            raise Exception("Cannot get folder name")

        transform('%s/%s' % (settings.CONTENT_DIR, folder_name),
                  None,
                  settings.DEFAULT_DOCS_VERSION,
                  options)

        sitemap_helper.generate_sitemap(settings.DEFAULT_DOCS_VERSION, 'en')
        sitemap_helper.generate_sitemap(settings.DEFAULT_DOCS_VERSION, 'zh')

        if content_id:
            # The default category for documentation is 'fluid'
            category = 'default'
            if content_id == Content.DOCUMENTATION:
                category = 'fluid'

            return _redirect_first_link_in_contents(request, settings.DEFAULT_DOCS_VERSION, content_id, category)
        else:
            return redirect('/')

    except Exception as e:
        return HttpResponseServerError("Cannot reload docs: %s" % e)


def _redirect_first_link_in_contents(request, version, content_id, category=None):
    """
    Given a version and a content service, redirect to the first link in it's
    navigation.
    """
    lang = portal_helper.get_preferred_language(request)

    # These are the repos without menus.
    if content_id in ['models', 'mobile']:
        navigation = None
        path = 'README.html'
        sitemap_dir = sitemap_helper._get_sitemap_path('', content_id)

    else:
        navigation, sitemap_dir = sitemap_helper.get_sitemap(
            version, lang, content_id)

    try:
        # Get the first section link from the content.
        # content = root_navigation[content_id]

        content_path = _get_content_prefix(
            sitemap_dir, content_id, lang, version)

        if navigation:
            path = _get_first_link_in_contents(navigation, lang)

        if not path:
            msg = 'Cannot perform reverse lookup on link: %s' % path
            raise Exception(msg)

        # TODO: Needs to be replaced with a reverse like in url_helper.append_prefix_to_path.

        # path = os.path.splitext(urlparse(path).path)[0] + '.html'
        # return redirect('%s/%s' % (content_path, path))
        return redirect(url_helper.get_html_page_path(content_path, path))

    except Exception as e:
        print e.message
        return redirect('/')


def _get_content_prefix(menu_path, content_id, lang, version):
    # Try to seek whether this content has been generated yet.
    workspace_path = os.path.join(settings.BASE_DIR, settings.WORKSPACE_DIR)

    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)

    content_prefix = url_helper.get_page_url_prefix(content_id, lang, version)
    content_path = '%s/%s' % (workspace_path, content_prefix)

    # If it hasn't, try generating it.
    if not os.path.exists(content_path):
        # Generate the directory.
        os.makedirs(content_path)

        transform(content_id, os.path.dirname(menu_path), content_path)

    return content_prefix


def _get_first_link_in_contents(navigation, lang):
    """
    Given a content's sitemap, and a language choice, get the first available link.
    """
    # if not category:
    #     category = 'default'

    # if navigation and 'categories' in navigation and category in navigation['categories']:
    #     navigation = navigation['categories'][category]

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
    #static_content_path = sitemap_helper.get_external_file_path(path)
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
        if content_id in [Content.MOBILE, Content.MODELS]:
            template = 'content_doc.html'

        response = render(request, template, context)
        return response


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
    # if settings.CURRENT_PPO_MODE == settings.PPO_MODES.DOC_EDIT_MODE:
    #     context = {
    #         'folder_names': portal_helper.get_available_doc_folder_names(),
    #     }
    #     return render(request, 'index_doc_mode.html', context)
    #
    # elif settings.CURRENT_PPO_MODE == settings.PPO_MODES.DOC_VIEW_MODE:
    #     if portal_helper.has_downloaded_workspace_file():
    #         preferred_version = portal_helper.get_preferred_version(request)
    #         return _redirect_first_link_in_contents(request, preferred_version, Content.DOCUMENTATION)
    #     else:
    #         response = render(request, 'index_doc_view_mode.html')
    #         portal_helper.set_preferred_version(response, 'develop')
    #         return response
    #
    # else:
    return render(request, 'index.html')


def cn_home_root(request):
    response = redirect('/')
    portal_helper.set_preferred_language(request, response, 'zh')
    return response


def book_home(request):
    return _redirect_first_link_in_contents(request, 'develop', Content.BOOK)

def about_en(request):
    return render(request, 'about_en.html')

def about_cn(request):
    return render(request, 'about_cn.html')


def content_home(request):
    path = request.path[1:]

    if '/' in path:
        path = path[0, path.index('/')]

    if '?' in path:
        path = path[0, path.index('?')]

    return _redirect_first_link_in_contents(
        request, portal_helper.get_preferred_version(request), path)


def download_latest_doc_workspace(request):
    portal_helper.download_and_extract_workspace()
    return redirect('/')


def blog_root(request):
    path = sitemap_helper.get_external_file_path('blog/index.html')

    return render(request, 'content.html', {
        'static_content': _get_static_content_from_template(path),
        'content_id': Content.BLOG
    })


def blog_sub_path(request, path):
    static_content_path = sitemap_helper.get_external_file_path(request.path)

    return render(request, 'content.html', {
        'static_content': _get_static_content_from_template(static_content_path),
        'content_id': Content.BLOG
    })


def content_sub_path(request, path=None):
    content_id = ''
    additional_context = {}

    if path.startswith(url_helper.DOCUMENTATION_ROOT):
        content_id = Content.DOCUMENTATION
        lang = portal_helper.get_preferred_language(request)

        search_url = '%s/%s/search.html' % (content_id, lang)
        if path.startswith(url_helper.DOCUMENTATION_ROOT + 'fluid'):
            search_url = '%s/fluid/%s/search.html' % (content_id, lang)

        additional_context = { 'allow_search': True, 'allow_version': True, 'search_url': search_url }

    elif path.startswith(url_helper.VISUALDL_ROOT):
        content_id = Content.VISUALDL

    elif path.startswith(url_helper.BOOK_ROOT):
        # content_id = Content.BOOK
        content_id = Content.DOCUMENTATION

    elif path.startswith(url_helper.MODEL_ROOT):
        # content_id = Content.MODELS
        content_id = Content.DOCUMENTATION

    elif path.startswith(url_helper.MOBILE_ROOT):
        # content_id = Content.MOBILE
        content_id = Content.DOCUMENTATION

    elif path.startswith(url_helper.API_ROOT):
        # content_id = Content.API
        content_id = Content.DOCUMENTATION

        search_url = '%s/%s/search.html' % (content_id, 'en')
        if path.startswith(url_helper.API_ROOT + 'fluid'):
            search_url = '%s/fluid/%s/search.html' % (content_id, 'en')

        additional_context = {'allow_search': True, 'allow_version': True, 'search_url': search_url}

    return _render_static_content(request, path, content_id, additional_context)


def content_root_path(request, path):
    content_id = ''
    path = path + '/'

    if path == url_helper.DOCUMENTATION_ROOT:
        content_id = Content.DOCUMENTATION

    elif path == url_helper.BOOK_ROOT:
        content_id = Content.BOOK

    elif path == url_helper.MODEL_ROOT:
        content_id = Content.MODELS

    elif path == url_helper.MOBILE_ROOT:
        content_id = Content.MOBILE

    return _redirect_first_link_in_contents(request, version, content_id)


def other_path(request, version, path=None):
    """
    Try to find the template associated with this path.
    """
    try:
        # If the template is found, render it.
        static_content_template = get_template(
            sitemap_helper.get_external_file_path(request.path))

    except TemplateDoesNotExist:
        # Else, fetch the page, and run through a generic stripper.
        fetch_and_transform(url_helper.GITHUB_ROOT + '/' + os.path.splitext(path)[0] + '.md', version)

    return _render_static_content(request, path, version, Content.OTHER)


def flush_other_page(request, version):
    """
    To clear the contents of any "cached" arbitrary markdown page, one can call
    *.paddlepaddle.org/docs/{version}/flush?link={...example.com/page.md}&key=123456
    """
    secret_subkey = request.GET.get('key', None)
    link = request.GET.get('link', None)

    if secret_subkey and secret_subkey == settings.SECRET_KEY[:6]:
        page_path = settings.OTHER_PAGE_PATH % (
            settings.EXTERNAL_TEMPLATE_DIR, version, os.path.splitext(
            urlparse(link).path)[0] + '.html')
        try:
            os.remove(page_path)
            return HttpResponse('Page successfully flushed.')

        except:
            return HttpResponse('Page to flush not found.')
