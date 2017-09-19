import os
import posixpath

from django.template.loader import get_template
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.utils.six.moves.urllib.parse import unquote
from django.contrib.staticfiles import finders

from django.http import Http404
from django.views import static

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

def book_root(request):
    path = settings.EXTERNAL_TEMPLATE_DIR + "/book/index.html"
    static_content_template = get_template(path)
    static_content = static_content_template.render()
    return render(request, 'tutorial.html', {'static_content': static_content})

def tutorial_root(request):
    path = 'tutorial.html'
    return render(request, path)

def blog_root(request):
    path = settings.EXTERNAL_TEMPLATE_DIR + "/blog/index.html"
    static_content_template = get_template(path)
    static_content = static_content_template.render()
    return render(request, 'blog.html', {'static_content': static_content})

def blog_sub_path(request, path):
    file_path = "%s/blog/%s" % (settings.EXTERNAL_TEMPLATE_DIR, path)
    static_content_template = get_template(file_path)
    static_content = static_content_template.render()
    return render(request, 'blog.html', {'static_content': static_content})

def documentation_root(request, language):
    path = "%s/documentation/%s/html/index.html" % (settings.EXTERNAL_TEMPLATE_DIR, language)
    static_content_template = get_template(path)
    static_content = static_content_template.render()
    return render(request, 'documentation.html', {'static_content': static_content})

def documentation_sub_path(request, language, path=None):
    path = "%s/documentation/%s/html/%s" % (settings.EXTERNAL_TEMPLATE_DIR, language, path)
    static_content_template = get_template(path)
    static_content = static_content_template.render()
    return render(request, 'documentation.html', {'static_content': static_content})

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

    print "CSS HANDLER! %s, %s" % (path, extension)
    if not settings.DEBUG and not insecure:
        raise Http404

    normalized_path = posixpath.normpath(unquote(path)).lstrip('/')
    print "normalized_path ROOT: %s" %(normalized_path)

    # absolute_path = finders.find(normalized_path)
    absolute_path = settings.EXTERNAL_TEMPLATE_DIR + "/" + append_path + normalized_path + "." + extension
    print "ABS ROOT: %s" %(absolute_path)
    if not absolute_path:
        if path.endswith('/') or path == '':
            raise Http404("Directory indexes are not allowed here.")
        raise Http404("'%s' could not be found" % path)
    document_root, path = os.path.split(absolute_path)
    return static.serve(request, path, document_root=document_root, **kwargs)