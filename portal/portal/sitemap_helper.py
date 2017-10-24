import json
import os
import collections
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseServerError

from portal import url_helper


def get_sitemap(version):
    cache_key = 'sitemap.%s' % version
    sitemap_cache = cache.get(cache_key, None)

    if not sitemap_cache:
        sitemap_cache = _load_sitemap_from_file(version)

        if sitemap_cache:
            timeout = settings.DEFAULT_CACHE_EXPIRY
            cache.set(cache_key, sitemap_cache, timeout)
        else:
            raise Exception("Cannot generate sitemap for version %s" % version)

    return sitemap_cache


def _load_sitemap_from_file(version):
    # TODO[thuan]: Remove code that caches sitemap file for now, need to find better way of doing this
    # sitemap = None
    # sitemap_path = _get_sitemap_path(version)
    # if os.path.isfile(sitemap_path):
    #     # Sitemap file exists, lets load it
    #     try:
    #         print "Loading sitemap from %s" % sitemap_path
    #         json_data = open(sitemap_path).read()
    #         sitemap = json.loads(json_data, object_pairs_hook=collections.OrderedDict)
    #     except Exception as e:
    #         print "Cannot load sitemap from file %s: %s" % (sitemap_path, e.message)
    #
    # if not sitemap:
    #     # We couldn't load sitemap.<version>.json file, lets generate it
    #     sitemap = generate_sitemap(version)

    return generate_sitemap(version)


def generate_sitemap(version):
    sitemap = None
    sitemap_template_path = "%s/assets/sitemaps/%s.json" % (settings.PROJECT_ROOT, version)

    try:
        json_data = open(sitemap_template_path).read()
        sitemap = json.loads(json_data, object_pairs_hook=collections.OrderedDict)
        sitemap = _resolve_references(sitemap, version)
        _transform_urls(version, sitemap)

        # TODO[thuan]: Remove code that caches sitemap file for now, need to find better way of doing this
        # sitemap_path = _get_sitemap_path(version)
        # with open(sitemap_path, 'w') as fp:
        #     json.dump(sitemap, fp)

    except Exception as e:
        print "Cannot generate sitemap from %s: %s" % (sitemap_template_path, e.message)

    return sitemap


def load_json_and_resolve_references(path, version):
    sitemap = None
    # TODO [Jeff Wang]: Update the path to the reference json
    sitemap_path = "%s/assets/sitemaps/%s" % (settings.PROJECT_ROOT, path)

    try:
        json_data = open(sitemap_path).read()
        sitemap = json.loads(json_data, object_pairs_hook=collections.OrderedDict)
        sitemap = _resolve_references(sitemap, version)

    except Exception as e:
        print "Cannot resolve sitemap from %s: %s" % (sitemap_path, e.message)

    return sitemap


def _resolve_references(navigation, version):
    if isinstance(navigation, list):
        # navigation is type list, resolved_navigation should also be type list
        resolved_navigation = []

        for item in navigation:
            resolved_navigation.append(_resolve_references(item, version))

        return resolved_navigation

    elif isinstance(navigation, dict):
        # navigation is type dict, resolved_navigation should also be type dict
        resolved_navigation = {}

        for key, value in navigation.items():
            if key == "$ref":
                # The value is the relative path to the associated json file
                referenced_json = load_json_and_resolve_references(value, version)
                resolved_navigation = referenced_json
            else:
                resolved_navigation[key] = _resolve_references(value, version)

        return resolved_navigation

    else:
        # leaf node: The type of navigation should be [string, int, float, unicode]
        return navigation


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

                chapter_link = {}
                if 'link' in chapter:
                    chapter_link = chapter['link']
                    for lang, url in chapter_link.items():
                        chapter_link[lang] = url_helper.append_prefix_to_path(version, chapter_link[lang])

                if 'sections' in chapter:
                    all_links = []
                    for section in chapter['sections']:
                        if 'link' in section:
                            link = section['link']
                            for lang, url in link.items():
                                link[lang] = url_helper.append_prefix_to_path(version, link[lang])
                                all_links.append(link[lang])
                                if not lang in chapter_link:
                                    chapter_link[lang] = link[lang]

                        if 'sub_sections' in section:
                            all_sub_section_links = []
                            for subsection in section['sub_sections']:
                                if 'link' in subsection:
                                    link = subsection['link']
                                    for lang, url in link.items():
                                        link[lang] = url_helper.append_prefix_to_path(version, link[lang])
                                        all_links.append(link[lang])
                                        all_sub_section_links.append(link[lang])
                                        if not lang in chapter_link:
                                            chapter_link[lang] = link[lang]

                            section['all_links'] = all_sub_section_links

                    chapter['all_links'] = all_links

                chapter['link'] = chapter_link


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
    return "%s/sitemap.%s.json" % (tempfile.gettempdir(), version)


def _get_chapter_path(version, module):
    return "%s/%s%s/site.json" % (settings.EXTERNAL_TEMPLATE_DIR, get_doc_subpath(version), module)


def get_available_versions():
    path = '%s/docs' % settings.EXTERNAL_TEMPLATE_DIR
    for root, dirs, files in os.walk(path):
        if root == path:
            return dirs


def get_external_file_path(sub_path):
    return "%s/%s" % (settings.EXTERNAL_TEMPLATE_DIR, sub_path)