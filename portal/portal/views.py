# -*- coding: utf-8 -*-
import os
import posixpath
import urllib
from urlparse import urlparse

from django.template.loader import get_template
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.six.moves.urllib.parse import unquote
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.views import static
from django.template import TemplateDoesNotExist
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.core.cache import cache

from portal import sitemap_helper, portal_helper, url_helper
from deploy.documentation import fetch_and_transform


# Search the path and render the content
# Return Page not found if the template is missing.
def _get_static_content_from_template(path):
    try:
        static_content_template = get_template(path)
        return static_content_template.render()
    except TemplateDoesNotExist:
        return "Page not found: %s" % path


def home_root(request):
    # if settings.DOC_MODE:
    #     return tutorial_root(request)
    # else:
    return render(request, 'index.html')


def change_version(request):
    preferred_version = request.GET.get('preferred_version', settings.DEFAULT_DOCS_VERSION)
    portal_helper.set_preferred_version(request, preferred_version)
    book_id = request.GET.get('book_id', None)

    lang = portal_helper.get_preferred_language(request)
    root_navigation = sitemap_helper.get_sitemap(preferred_version, lang)

    if book_id:
        return _redirect_first_link_in_book(request, preferred_version, book_id)
    elif root_navigation and len(root_navigation) > 0:
        for book_id, book in root_navigation.items():
            if book:
                return _redirect_first_link_in_book(request, preferred_version, book_id)

    return home_root(request)


def change_lang(request):
    lang = request.GET.get('lang_code', 'en')

    response = redirect('/')
    # Needs to set the preferred language first in case the following code reads lang from portal_helper
    portal_helper.set_preferred_language(request, response, lang)

    from_path = urllib.unquote(request.GET.get('path', None))

    if from_path:
        # Get which book the user was reading.
        book_id = request.GET.get('book_id')

        if book_id:
            # Get the proper version
            docs_version = portal_helper.get_preferred_version(request)
            # Find the translated path
            translated_path = _get_translated_link_in_book(book_id, docs_version, from_path, lang)

            if translated_path:
                response = redirect(translated_path)
            else:
                # There is no translated path. Use the first link in the book instead
                response = _redirect_first_link_in_book(request, docs_version, book_id)

        elif from_path.startswith('/blog'):
            # Blog doesn't a book_id and translated version. Simply redirect back to the original path
            response = redirect(from_path)

    portal_helper.set_preferred_language(request, response, lang)
    return response


def blog_root(request):
    path = sitemap_helper.get_external_file_path('blog/index.html')

    context = {
        'static_content': _get_static_content_from_template(path)
    }
    return render(request, 'blog.html', context)


def blog_sub_path(request, path):
    static_content_path = sitemap_helper.get_external_file_path(request.path)

    context = {
        'static_content': _get_static_content_from_template(static_content_path)
    }

    return render(request, 'blog.html', context)


def content_root(request, version, book_id):
    return _redirect_first_link_in_book(request, version, book_id)


def book_sub_path(request, version, path=None):
    return _render_static_content(request, version, 'tutorial', 'book')


def documentation_path(request, version, path=None):
    # Since only the API section of docs is in "Documentation" book, we only use the "documentation.html" template for
    # URLs with /api/ in the path.  Otherwise we use "tutorial.html" template
    lang = portal_helper.get_preferred_language(request)
    template = 'documentation'     # TODO[thuan]: do this in a less hacky way
    allow_search = True

    search_url = None
    if allow_search:
        # TODO[thuan]: Implement proper full text search
        search_url = '%s/search.html' % lang
    extra_context =  { 'allow_search': allow_search, 'search_url': search_url }
    return _render_static_content(request, version, template, 'docs', extra_context)


def models_path(request, version, path=None):
    return _render_static_content(request, version, 'models', None)


def other_path(request, version, path=None):
    # Try to find the template associated with this path.
    try:
        # If the template is found, render it.
        static_content_template = get_template(
            sitemap_helper.get_external_file_path(request.path))

    except TemplateDoesNotExist:
        # Else, fetch the page, and run through a generic stripper.
        fetch_and_transform(url_helper.GITHUB_ROOT + '/' + os.path.splitext(path)[0] + '.md', version)

    return _render_static_content(request, version, 'tutorial', 'other')


def flush_other_page(request, version):
    """
    To clear the contents of any "cached" arbitrary markdown page, one can call
    *.paddlepaddle.org/docs/{version}/flush?link={...example.com/page.md}&key=123456
    """
    secret_subkey = request.GET.get('key', None)
    link = request.GET.get('link', None)

    if secret_subkey and secret_subkey == settings.SECRET_KEY[:6]:
        page_path = '%s/docs/%s/other/%s' % (
            settings.EXTERNAL_TEMPLATE_DIR, version, os.path.splitext(
            urlparse(link).path)[0] + '.html')
        try:
            os.remove(page_path)
            return HttpResponse('Page successfully flushed.')

        except:
            return HttpResponse('Page to flush not found.')


def _redirect_first_link_in_book(request, version, book_id):
    portal_helper.set_preferred_version(request, version)
    lang = portal_helper.get_preferred_language(request)
    root_navigation = sitemap_helper.get_sitemap(version, lang)

    try:
        # Get the first section link from book
        path = None
        book = root_navigation[book_id]
        path = _get_first_link_in_book(book, lang)

        if not path:
            print "Cannot perform reverse lookup on link: %s" % path
            return HttpResponseServerError()

        return redirect(path)
    except Exception as e:
        return HttpResponseServerError("Cannot get book root url: %s" % e.message)


def _render_static_content(request, version, book_id, content_src, additional_context=None):
    if version:
        portal_helper.set_preferred_version(request, version)

    static_content_path = sitemap_helper.get_external_file_path(request.path)

    context = {
        'static_content': _get_static_content_from_template(static_content_path),
        'book_id': book_id,
        'content_src': content_src
    }

    if additional_context:
        context.update(additional_context)

    return render(request, 'content.html', context)


def _get_first_link_in_book(book, lang):
    path = None

    if book:
        first_chapter = None
        if book and 'sections' in book and len(book['sections'])>0:
            first_chapter = book['sections'][0]
        if first_chapter and 'link' in first_chapter:
            path = first_chapter['link'][lang]
        elif first_chapter and ('sections' in first_chapter) and len(first_chapter['sections']) > 0:
            first_section = first_chapter['sections'][0]
            path = first_section['link'][lang]

    return path


def _get_translated_link_in_book(book_id, version, target_link, lang):
    side_nav_content = sitemap_helper.get_book_navigation(
        book_id,
        version,
        lang
    )

    translated_path = ""
    # Go through each level, and find the matching URL,
    # Once found, check if there is translated link
    for chapter_id, chapter in side_nav_content.iteritems():
        if 'sections' in chapter:
            for section in chapter['sections']:

                if 'link' in section:
                    link = section['link']
                    if target_link in link.values():
                        if lang in link:
                            translated_path = link[lang]
                            break

                elif 'sub_sections' in section:
                    for sub_section in section['sub_sections']:
                        if 'link' in sub_section:
                            link = sub_section['link']
                            if target_link in link.values():
                                if lang in link:
                                    translated_path = link[lang]
                                    break

    return translated_path


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
    append_path = ""

    if not settings.DEBUG and not insecure:
        raise Http404

    normalized_path = posixpath.normpath(unquote(path)).lstrip('/')

    # absolute_path = finders.find(normalized_path)
    absolute_path = settings.EXTERNAL_TEMPLATE_DIR + "/" + append_path + normalized_path + "." + extension
    if not absolute_path:
        if path.endswith('/') or path == '':
            raise Http404("Directory indexes are not allowed here.")
        raise Http404("'%s' could not be found" % path)
    document_root, path = os.path.split(absolute_path)
    return static.serve(request, path, document_root=document_root, **kwargs)
