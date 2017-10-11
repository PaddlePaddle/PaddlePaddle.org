# -*- coding: utf-8 -*-
import os
import posixpath

from django.template.loader import get_template
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.six.moves.urllib.parse import unquote
from django.http import Http404, HttpResponseServerError
from django.views import static
from django.template import TemplateDoesNotExist
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.core.cache import cache

from portal import sitemap_helper, portal_helper, url_helper


# Search the path and render the content
# Return Page not found if the template is missing.
def _get_static_content_from_template(path):
    try:
        static_content_template = get_template(path)
        return static_content_template.render()
    except TemplateDoesNotExist:
        return "Page not found: %s" % path


def home_root(request):
    if settings.DOC_MODE:
        return tutorial_root(request)
    else:
        return render(request, 'index.html')


def change_version(request):
    preferred_version = request.GET.get('preferred_version', settings.DEFAULT_DOC_VERSION)
    portal_helper.set_preferred_version(request, preferred_version)

    return tutorial_root(request, preferred_version)


def change_lang(request):
    lang = request.GET.get('lang_code', 'en')

    response = redirect('/')
    portal_helper.set_preferred_language(request, response, lang)

    return response


def blog_root(request):
    path = sitemap_helper.get_external_file_path('blog/index.html')

    context = {
        'static_content': _get_static_content_from_template(path)
    }
    return render(request, 'blog.html', context)


def blog_sub_path(request, path):
    return _render_static_content(request, None, 'blog.html')


def tutorial_root(request, version):
    return _redirect_first_link_in_book(request, version, 'tutorial')


def book_sub_path(request, version, path=None):
    return _render_static_content(request, version, 'tutorial.html')


def documentation_root(request, version):
    return _redirect_first_link_in_book(request, version, 'documentation')


def documentation_path(request, version, path=None):
    # Since we only API section of docs is in "Documentation" book, we only use the "documentation.html" template for
    # URLs with /api/ in the path.  Otherwise we use "tutorial.html" template
    template = 'documentation.html'     # TODO[thuan]: do this in a less hacky way
    if '/api/' not in path:
        template = 'tutorial.html'

    return _render_static_content(request, version, template)


def models_path(request, version, path=None):
    return _render_static_content(request, version, 'documentation.html')


def _redirect_first_link_in_book(request, version, book_id):
    portal_helper.set_preferred_version(request, version)
    lang = portal_helper.get_preferred_language(request)
    root_navigation = sitemap_helper.get_sitemap(version)

    try:
        # Get the first section link from the tutorial book
        path = None
        book = root_navigation[book_id]
        path = _get_first_link_in_book(book, lang)

        if not path:
            print "Cannot perform reverse lookup on link: %s" % path
            return HttpResponseServerError()

        return redirect(path)
    except Exception as e:
        return HttpResponseServerError("Cannot get book root url: %s" % e.message)


def _render_static_content(request, version, template):
    if version:
        portal_helper.set_preferred_version(request, version)

    static_content_path = sitemap_helper.get_external_file_path(request.path)

    context = {
        'static_content': _get_static_content_from_template(static_content_path)
    }

    return render(request, template, context)


def _get_first_link_in_book(book, lang):
    path = None

    if book:
        if book and len(book) > 0:
            _, first_chapter = book.items()[0]
        if first_chapter and ('sections' in first_chapter) and len(first_chapter['sections']) > 0:
            first_section = first_chapter['sections'][0]
            path = first_section['link'][lang]

    return path


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
