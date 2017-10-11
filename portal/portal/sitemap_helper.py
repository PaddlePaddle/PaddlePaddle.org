import json
import os
import collections

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseServerError

from portal import url_helper


def get_sitemap(version):
    version = version.strip("/")    # TODO[thuan]: sometimes version comes in with a leading or trailing slash, need to figure out why
    cache_key = 'sitemap.%s' % version
    sitemap_cache = cache.get(cache_key, None)

    if not sitemap_cache:
        sitemap_cache = _load_sitemap_from_file(version)
        _transform_urls(version, sitemap_cache)

        if sitemap_cache:
            timeout = 5 if settings.DEBUG else 60
            cache.set(cache_key, sitemap_cache, timeout)
        else:
            raise Exception("Cannot generate sitemap for version %s" % version)

    return sitemap_cache


def _load_sitemap_from_file(version):
    sitemap = None

    file_path = _get_sitemap_path(version)
    if os.path.isfile(file_path):
        # Sitemap file exists, lets load it
        try:
            print "Loading sitemap from %s" % file_path
            json_data = open(file_path).read()
            sitemap = json.loads(json_data, object_pairs_hook=collections.OrderedDict)
        except Exception as e:
            print "Cannot load sitemap from file %s: %s" % (file_path, e.message)
    else:
        msg = "Cannot load sitemap from file %s" % file_path
        print msg
        raise Exception(msg)

    return sitemap


def _transform_urls(version, sitemap):
    '''
    Since paths defined in assets/sitemaps/<version>.json are defined relative to the folder structure of the content
    directories, we will need to append the URL path prefix so our URL router knows how to resolve the URLs.

    ex:
    /documentation/en/getstarted/index_en.html -> /docs/<version>/documentation/en/gettingstarted/index_en.html
    /book/01.fit_a_line/index.html -> /docs/<version>/book/01.fit_a_line/index.html

    :param version:
    :param sitemap:
    :return:
    '''
    if sitemap:
        for _, book in sitemap.items():
            for _, chapter in book.items():
                if 'sections' in chapter:
                    for section in chapter['sections']:
                        if 'link' in section:
                            link = section['link']
                            for lang, url in link.items():
                                link[lang] = url_helper.append_prefix_to_path(version, link[lang])


# Merge all site.json files
def _load_all_sections(version):
    # Load from the externalTemplates
    module_list = ["book", "documentation"]

    all_sections = {}
    for module_name in module_list:
        chapter_path = _get_chapter_path(version, module_name)
        try:
            chapter_data = open(chapter_path).read()
            chapter = json.loads(chapter_data)

            for key, value in chapter.iteritems():
                all_sections["%s.%s" % (module_name, key)] = value
        except:
            print "Missing site.json from %s" % chapter_path

    return all_sections


def get_book_navigation(book_id, version):
    root_nav = get_sitemap(version)
    return root_nav.get(book_id, None)


def get_doc_subpath(version):
    return "docs/%s/" % version


def _get_book_path(version):
    return "%s/%ssite.json" % (settings.EXTERNAL_TEMPLATE_DIR, get_doc_subpath(version))


def _get_sitemap_path(version):
    return "%s/assets/sitemaps/%s.json" % (settings.PROJECT_ROOT, version)


def _get_chapter_path(version, module):
    return "%s/%s%s/site.json" % (settings.EXTERNAL_TEMPLATE_DIR, get_doc_subpath(version), module)


def get_available_versions():
    path = '%s/docs' % settings.EXTERNAL_TEMPLATE_DIR
    for root, dirs, files in os.walk(path):
        if root == path:
            return dirs


def get_external_file_path(sub_path):
    return "%s/%s" % (settings.EXTERNAL_TEMPLATE_DIR, sub_path)