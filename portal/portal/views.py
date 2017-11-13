# -*- coding: utf-8 -*-
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

from portal import sitemap_helper, portal_helper, url_helper
from deploy.documentation import transform, fetch_and_transform
from portal import url_helper
from portal_helper import Content

def change_version(request):
    """
    Change current documentation version.
    """
    # Look for a new version in the URL get params.
    preferred_version = request.GET.get('preferred_version', settings.DEFAULT_DOCS_VERSION)

    # Refers to the name of the contents service, for eg. 'models', 'documentation', or 'book'.
    content_id = request.GET.get('content_id', None)

    # Infer language based on session/cookie.
    lang = portal_helper.get_preferred_language(request)

    root_navigation = sitemap_helper.get_sitemap(preferred_version, lang)

    response = home_root(request)

    if content_id:
        if content_id in root_navigation and root_navigation[content_id]:
            response = _redirect_first_link_in_contents(request, preferred_version, content_id)
        else:
            # This version doesn't support this book. Redirect it back to home
            response = redirect('/')

    # If no content service specified, just redirect to first page of root site navigation.
    elif root_navigation and len(root_navigation) > 0:
        for content_id, content in root_navigation.items():
            if content:
                response = _redirect_first_link_in_contents(request, preferred_version, content_id)

    portal_helper.set_preferred_version(request, response, preferred_version)

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
                  settings.DEFAULT_DOCS_VERSION)

        sitemap_helper.generate_sitemap(settings.DEFAULT_DOCS_VERSION, 'en')
        sitemap_helper.generate_sitemap(settings.DEFAULT_DOCS_VERSION, 'zh')

        if content_id:
            return _redirect_first_link_in_contents(request, settings.DEFAULT_DOCS_VERSION, content_id)
        else:
            return redirect('/')

    except Exception as e:
        return HttpResponseServerError("Cannot reload docs: %s" % e)


def _redirect_first_link_in_contents(request, version, content_id):
    """
    Given a version and a content service, redirect to the first link in it's
    navigation.
    """
    lang = portal_helper.get_preferred_language(request)
    root_navigation = sitemap_helper.get_sitemap(version, lang)

    try:
        # Get the first section link from the content.
        content = root_navigation[content_id]
        path = _get_first_link_in_contents(content, lang)

        if not path:
            msg = 'Cannot perform reverse lookup on link: %s' % path
            raise Exception(msg)

        response = redirect(path)
        portal_helper.set_preferred_version(request, response, version)
        return redirect(path)

    except Exception as e:
        print e.message
        return redirect('/')


def _get_first_link_in_contents(content, lang):
    """
    Given a content's sitemap, and a language choice, get the first available link.
    """
    if content:
        # If there are sections in the root of the sitemap.
        first_chapter = None
        if content and 'sections' in content and len(content['sections']) > 0:
            first_chapter = content['sections'][0]

        # If there is a known root "section" with links.
        if first_chapter and 'link' in first_chapter:
            return first_chapter['link'][lang]

        # Or if there is a known root section with subsections with links.
        elif first_chapter and ('sections' in first_chapter) and len(first_chapter['sections']) > 0:
            first_section = first_chapter['sections'][0]
            return first_section['link'][lang]

        # Last option is to attempt to see if there is only one link on the title level.
        elif 'link' in content:
            return content['link'][lang]


def _get_translated_link_in_content(content_id, version, target_link, lang):
    """
    For a given content service and version and link, return a related page in
    the desired language.
    """
    side_nav_content = sitemap_helper.get_content_navigation(content_id, version, lang)

    # Go through each level, and find the matching URL,
    # Once found, check if there is translated link.
    # NOTE: Only 3 levels of sections nesting are supported right now.
    for chapter_id, chapter in side_nav_content.iteritems():
        if 'sections' in chapter:
            for section in chapter['sections']:
                if 'link' in section:
                    link = section['link']
                    if target_link in link.values():
                        if lang in link:
                            return link[lang]

                elif 'sections' in section:
                    for sub_section in section['sections']:
                        if 'link' in sub_section:
                            link = sub_section['link']
                            if target_link in link.values():
                                if lang in link:
                                    return link[lang]


def static_file_handler(request, path, extension, insecure=False, **kwargs):
    """
    Note: This is static handler is only used during development.  In production, the Docker image uses NGINX to serve
    static content.

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

    absolute_path = settings.EXTERNAL_TEMPLATE_DIR + '/' + append_path + normalized_path + '.' + extension
    if not absolute_path:
        if path.endswith('/') or path == '':
            raise Http404('Directory indexes are not allowed here.')

        raise Http404('\'%s\' could not be found' % path)

    document_root, path = os.path.split(absolute_path)
    return static.serve(request, path, document_root=document_root, **kwargs)


def _render_static_content(request, version, content_id, additional_context=None):
    """
    This is the primary function that renders all static content (.html) pages.
    It builds the context and passes it to the only documentation template rendering template.
    """

    static_content_path = sitemap_helper.get_external_file_path(request.path)

    context = {
        'static_content': _get_static_content_from_template(static_content_path),
        'content_id': content_id,
    }

    if additional_context:
        context.update(additional_context)

    template = 'content_panel.html'
    if content_id in [Content.MOBILE, Content.MODELS]:
        template = 'content_doc.html'

    response = render(request, template, context)
    if version:
        portal_helper.set_preferred_version(request, response, version)

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
    if settings.CURRENT_PPO_MODE == settings.PPO_MODES.DOC_EDIT_MODE:
        context = {
            'folder_names': portal_helper.get_available_doc_folder_names()
        }
        return render(request, 'index_doc_mode.html', context)

    elif settings.CURRENT_PPO_MODE == settings.PPO_MODES.DOC_VIEW_MODE:
        if portal_helper.has_downloaded_workspace_file():
            preferred_version = portal_helper.get_preferred_version(request)
            return _redirect_first_link_in_contents(request, preferred_version, Content.DOCUMENTATION)
        else:
            response = render(request, 'index_doc_view_mode.html')
            portal_helper.set_preferred_version(request, response, 'develop')
            return response

    else:
        return render(request, 'index.html')


def download_latest_doc_workspace(request):
    portal_helper.download_and_extract_workspace()
    return redirect('/')


def blog_root(request):
    path = sitemap_helper.get_external_file_path('blog/index.html')

    return render(request, 'content.html', {
        'static_content': _get_static_content_from_template(path),
        'content_id': 'Blog'
    })


def blog_sub_path(request, path):
    static_content_path = sitemap_helper.get_external_file_path(request.path)

    return render(request, 'content.html', {
        'static_content': _get_static_content_from_template(static_content_path),
        'content_id': 'Blog'
    })


def content_sub_path(request, version, path=None):
    content_id = ''
    additional_context = None

    if path.startswith(url_helper.DOCUMENTATION_ROOT):
        content_id = Content.DOCUMENTATION
        lang = portal_helper.get_preferred_language(request)
        search_url = '%s/%s/search.html' % (content_id, lang)
        additional_context = { 'allow_search': True, 'search_url': search_url }

    elif path.startswith(url_helper.BOOK_ROOT):
        content_id = Content.BOOK

    elif path.startswith(url_helper.MODEL_ROOT):
        content_id = Content.MODELS

    elif path.startswith(url_helper.MOBILE_ROOT):
        content_id = Content.MOBILE

    return _render_static_content(request, version, content_id, additional_context)


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

    return _render_static_content(request, version, Content.OTHER)


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
