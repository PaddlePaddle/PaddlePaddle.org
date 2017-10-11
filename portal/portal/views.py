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
    path = sitemap_helper.get_external_file_path(request.path)

    context = {
        'static_content': _get_static_content_from_template(path)
    }
    return render(request, 'blog.html', context)


def tutorial_root(request, version):
    portal_helper.set_preferred_version(request, version)
    lang = portal_helper.get_preferred_language(request)
    root_navigation = sitemap_helper.get_sitemap(version)

    try:
        # Get the first section link from the tutorial book
        path = None
        tutorial = root_navigation['tutorial']
        path = _get_first_link_in_book(tutorial, lang)

        if not path:
            print "Cannot perform reverse lookup on link: %s" % path
            return HttpResponseServerError()

        return redirect(path)
    except Exception as e:
        return HttpResponseServerError("Cannot get tutorial root url: %s" % e.message)



def book_sub_path(request, version, path):
    portal_helper.set_preferred_version(request, version)
    static_content_path = sitemap_helper.get_external_file_path(request.path)
    static_content = _get_static_content_from_template(static_content_path)

    context = {
        'static_content': static_content
    }

    return render(request, 'tutorial.html', context)


def documentation_root(request, version):
    portal_helper.set_preferred_version(request, version)
    lang = portal_helper.get_preferred_language(request)
    root_navigation = sitemap_helper.get_sitemap(version)

    try:
        # Get the first section link from the tutorial book
        path = None
        documentation = root_navigation['documentation']
        path = _get_first_link_in_book(documentation, lang)

        if not path:
            print "Cannot perform reverse lookup on link: %s" % path
            return HttpResponseServerError()

        return redirect(path)
    except Exception as e:
        return HttpResponseServerError("Cannot get documentation root url: %s" % e.message)


def documentation_path(request, version, path=None):
    portal_helper.set_preferred_version(request, version)
    static_content_path = sitemap_helper.get_external_file_path(request.path)

    context = {
        'static_content': _get_static_content_from_template(static_content_path)
    }

    template = 'documentation.html'     # TODO[thuan]: do this in a less hacky way
    if '/api/' not in path:
        template = 'tutorial.html'

    return render(request, template, context)


def models_path(request, version, path):
    portal_helper.set_preferred_version(request, version)
    static_content_path = sitemap_helper.get_external_file_path(request.path)

    context = {
        'static_content': _get_static_content_from_template(static_content_path)
    }

    return render(request, 'documentation.html', context)


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
