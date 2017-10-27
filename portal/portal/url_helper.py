from urlparse import urlparse
import os
import re

from django.conf import settings, urls
from django.core.urlresolvers import reverse


BLOG_ROOT = 'blog/'
BOOK_ROOT = 'book/'
DOCUMENTATION_ROOT = 'documentation/'
MODEL_ROOT = 'models/'
GITHUB_ROOT = 'https://raw.githubusercontent.com'

URL_NAME_CONTENT_ROOT = 'content_root'
URL_NAME_BLOG_ROOT = 'blog_root'
URL_NAME_DOCS_ROOT = "docs_root"
URL_NAME_DOCS = 'docs_path'
URL_NAME_TUTORIAL_ROOT = 'tutorial_root'
URL_NAME_TUTORIAL = 'tutorial_path'
URL_NAME_MODEL = 'model_path'
URL_NAME_OTHER = 'other_path'

def append_prefix_to_path(version, path):
    url = None

    if path:
        sub_path = None
        url_name = None

        path = path.strip("/")
        if path.startswith(DOCUMENTATION_ROOT):
            url_name = URL_NAME_DOCS
            sub_path = path[len(DOCUMENTATION_ROOT):]
        elif path.startswith(BOOK_ROOT):
            url_name = URL_NAME_TUTORIAL
            sub_path = path[len(BOOK_ROOT):]
        elif path.startswith(MODEL_ROOT):
            url_name = URL_NAME_MODEL
            sub_path = path[len(MODEL_ROOT):]
        elif path.startswith(GITHUB_ROOT):
            url_name = URL_NAME_OTHER
            sub_path = os.path.splitext(urlparse(path).path[1:])[0] + '.html'

        if sub_path and url_name:
            url = reverse(url_name, args=[version, sub_path])
            # reverse method escapes #, which breaks when we try to find it in the file system.  We unescape it here
            url = url.replace('%23', "#")
        else:
            print 'Cannot append prefix to version %s, path %s' % (version, path)

    return url


def link_cache_key(path):
    # Remove all language specific strings
    key = re.sub(r'[._]?(en|cn|zh)\.htm[l]?$', '', path)
    key = key.replace('/en/', '/')
    key = key.replace('/zh/', '/')

    return key