import re
from urlparse import urlparse

from django.core.urlresolvers import reverse

BLOG_ROOT = 'blog/'
BOOK_ROOT = 'book/'
DOCUMENTATION_ROOT = 'documentation/'
API_ROOT = 'api/'
MODEL_ROOT = 'models/'
MOBILE_ROOT = 'mobile/'
VISUALDL_ROOT = 'visualdl/'
GITHUB_ROOT = 'https://raw.githubusercontent.com'

URL_NAME_CONTENT_ROOT = 'content_root'
URL_NAME_CONTENT = 'content_path'
URL_NAME_BLOG_ROOT = 'blog_root'
URL_NAME_BOOK_ROOT = 'book_root'
URL_NAME_OTHER = 'other_path'


def append_prefix_to_path(version, path):
    """
    The path in the sitemap generated is relative to the location of the file
    in the repository it is fetched from. Based on the URL pattern of the
    organization of contents on the website (which is tied to how contents are
    transformed and stored after being pulled from repositories), these paths
    evolve. This function sets the path in the navigation for where the static
    content pages will get resolved.
    """
    url = None

    if path:
        path = path.strip('/')

        if path.startswith(GITHUB_ROOT):
            url_name = URL_NAME_OTHER
            sub_path = os.path.splitext(urlparse(path).path[1:])[0] + '.html'
        else:
            url_name = URL_NAME_CONTENT
            sub_path = path

        url = reverse(url_name, args=[version, sub_path])
        # reverse method escapes #, which breaks when we try to find it in the file system.  We unescape it here
        url = url.replace('%23', '#')

    return url


def link_cache_key(path):
    # Remove all language specific strings
    key = re.sub(r'[._]?(en|cn|zh)?\.htm[l]?$', '', path)
    key = key.replace('/en/', '/')
    key = key.replace('/zh/', '/')

    return key
