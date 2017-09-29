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


# Search the path and render the content
# Return Page not found if the template is missing.
def _get_static_content_from_template(path):
    try:
        static_content_template = get_template(path)
        return static_content_template.render()
    except TemplateDoesNotExist:
        return "Page not found"


def catch_all_handler(request, path=None):
    print "Catch All %s" % path

    base_template = '_base_nav.html'
    if request.GET.get("iframe", '0') == '1':
        base_template = '_base.html'

    # Resolve path based on template.

    if path:
        # if '/' in path:
        #     return render(request, settings.CONTENT_DIR + '/' + path + '.html', {
        #         'path': path
        #     })
        # else:
        # Return the index of the app's documentation.

        # TODO: Test nested paths to make sure they pull correctly
        static_content_template = get_template(path)

        return render(request, base_template, {'static_content': static_content_template.render()})


def home_root(request):
    current_lang_code = request.LANGUAGE_CODE
    lang_def = {}
    if current_lang_code:
        if current_lang_code == "en":
            lang_def['label'] = u"中文"
            lang_def['link'] = "/zh/"
        else:
            lang_def['label'] = "English"
            lang_def['link'] = "/en/"

    return render(request, 'index.html', {'lang_def': lang_def})

def book_sub_path(request, path):
    path = "%s/book/%s" % (settings.EXTERNAL_TEMPLATE_DIR, path)
    static_content = _get_static_content_from_template(path)

    context = {
        'static_content': static_content
    }

    return render(request, 'tutorial.html', context)

def tutorial_root(request):
    return redirect('/documentation/develop/en/html/getstarted/index_en.html')

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
    path = "%s/documentation/%s/%s/html/index.html" % (settings.EXTERNAL_TEMPLATE_DIR, version, language)

    context = {
        'static_content': _get_static_content_from_template(path),
        'request': request
    }
    return render(request, 'tutorial.html', context)


def documentation_sub_path(request, version,  language, path=None):
    path = "%s/documentation/%s/%s/html/%s" % (settings.EXTERNAL_TEMPLATE_DIR, version, language, path)

    context = {
        'static_content': _get_static_content_from_template(path),
        'version': version,
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
