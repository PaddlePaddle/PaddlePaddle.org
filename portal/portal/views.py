# -*- coding: utf-8 -*-
import os
import posixpath

from django.template.loader import get_template
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils.six.moves.urllib.parse import unquote
from django.http import Http404
from django.views import static
from django.template import TemplateDoesNotExist
from django.utils.translation import LANGUAGE_SESSION_KEY

from portal import sitemap_helper


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


def book_sub_path(request, version, path):
    path = "%s/%sbook/%s" % (settings.EXTERNAL_TEMPLATE_DIR, sitemap_helper.get_doc_subpath(version), path)
    static_content = _get_static_content_from_template(path)

    context = {
        'static_content': static_content
    }

    return render(request, 'tutorial.html', context)


def change_version(request):
    preferred_version = request.GET.get('preferred_version', settings.DEFAULT_DOC_VERSION)
    sitemap_helper.set_preferred_version(request, preferred_version)
    return tutorial_root(request)


def change_lang(request):
    lang = request.GET.get('lang_code', 'en')

    request.session[LANGUAGE_SESSION_KEY] = lang
    response = redirect('/')
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)

    return response


def tutorial_root(request):
    root_navigation = sitemap_helper.get_sitemap(sitemap_helper.get_preferred_version(request))
    tutorial_nav = root_navigation['tutorial']['root_url']
    return redirect(tutorial_nav)


def blog_root(request):
    path = settings.EXTERNAL_TEMPLATE_DIR + "/blog/index.html"

    context = {
        'static_content': _get_static_content_from_template(path)
    }
    return render(request, 'blog.html', context)


def blog_sub_path(request, path):
    path = "%s/blog/%s" % (settings.EXTERNAL_TEMPLATE_DIR, path)

    context = {
        'static_content': _get_static_content_from_template(path)
    }
    return render(request, 'blog.html', context)


def documentation_root(request, version, language):
    path = "%s/%sdocumentation/%s/html/index.html" % \
           (settings.EXTERNAL_TEMPLATE_DIR, sitemap_helper.get_doc_subpath(version), language)

    context = {
        'static_content': _get_static_content_from_template(path),
        'request': request
    }
    return render(request, 'tutorial.html', context)


def documentation_sub_path(request, version, language, path=None):
    path = "%s/%sdocumentation/%s/html/%s" % \
           (settings.EXTERNAL_TEMPLATE_DIR, sitemap_helper.get_doc_subpath(version), language, path)

    context = {
        'static_content': _get_static_content_from_template(path)
    }

    template = 'documentation.html'     # TODO[thuan]: do this in a less hacky way
    if '/api/' not in path:
        template = 'tutorial.html'

    return render(request, template, context)


def models_root(request, version):
    path = "%s/models/index/index.html" % settings.EXTERNAL_TEMPLATE_DIR

    context = {
        'static_content': _get_static_content_from_template(path),
        'version': version
    }
    return render(request, 'documentation.html', context)

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
