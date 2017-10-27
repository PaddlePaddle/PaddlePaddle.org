import json
import os
import collections
import tempfile
import traceback
import re

from django.conf import settings
from django.core.cache import cache

from portal import url_helper


def get_sitemap(version, language):
    """
    Given a version and language, fetch the sitemap for all contents from the
    cache, if available, or load them from the pre-compiled sitemap.
    """
    cache_key = 'sitemap.%s.%s' % (version, language)
    sitemap_cache = cache.get(cache_key, None)

    if not sitemap_cache:
        sitemap_cache = _load_sitemap_from_file(version, language)

        if sitemap_cache:
            cache.set(cache_key, sitemap_cache)
        else:
            raise Exception('Cannot generate sitemap for version %s' % version)

    return sitemap_cache


def _load_sitemap_from_file(version, language):
    """
    [For now] Returns a freshly generated sitemap file, given a version and language.
    """
    sitemap = None
    sitemap_path = _get_sitemap_path(version, language)

    if os.path.isfile(sitemap_path):
        # Sitemap file exists, lets load it
        try:
            # TODO[thuan]: Lets fix this in the next request (or remove it)
            # The temp file location may be different for each process.  So if we try to
            # regenerate it from python manage.py, it may not overwrite the sitemap
            # from the server
            pass
            # print "Loading sitemap from %s" % sitemap_path
            # json_data = open(sitemap_path).read()
            # sitemap = json.loads(json_data, object_pairs_hook=collections.OrderedDict)
        except Exception as e:
            print 'Cannot load sitemap from file %s: %s' % (sitemap_path, e.message)

    if not sitemap:
        # We couldn't load sitemap.<version>.json file, lets generate it
        sitemap = generate_sitemap(version, language)

    return sitemap


def generate_sitemap(version, language):
    """
    Using a sitemap template, generated a full sitemap using individual content
    sitemaps.
    """
    sitemap = None
    sitemap_template_path = '%s/assets/sitemaps/sitemap_tmpl.json' % settings.PROJECT_ROOT

    try:
        # Read the sitemap template.
        with open(sitemap_template_path) as json_data:
            sitemap = json.loads(json_data.read(), object_pairs_hook=collections.OrderedDict)

            # Resolve JSON references with contents' individual sitemaps.
            sitemap = _resolve_references(sitemap, version, language)

            # Change URLs to represent accurate URL paths and not references to repo directory structures.
            _transform_urls(version, sitemap, language)

            sitemap_path = _get_sitemap_path(version, language)

        # Write the built sitemaps to the main sitemap file the app reads.
        with open(sitemap_path, 'w') as fp:
            json.dump(sitemap, fp)

    except Exception as e:
        print 'Cannot generate sitemap from %s: %s' % (sitemap_template_path, e.message)
        traceback.print_exc()

    return sitemap


def load_json_and_resolve_references(path, version, language):
    """
    Loads any sitemap file (content root or site's root sitemap), and resolves
    references to generate a combined sitemap dictionary.
    """
    sitemap = None
    sitemap_path = '%s/docs/%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, version, path)

    try:
        with open(sitemap_path) as json_data:
            sitemap = json.loads(json_data.read(), object_pairs_hook=collections.OrderedDict)

        # Resolve any reference in inner sitemap files.
        sitemap = _resolve_references(sitemap, version, language)
    except Exception as e:
        print 'Cannot resolve sitemap from %s: %s' % (sitemap_path, e.message)

    return sitemap


def _resolve_references(navigation, version, language):
    """
    Iterates through an object (could be a dict, list, str, int, float, unicode, etc.)
    and if it finds a dict with `$ref`, resolves the reference by loading it from
    the respective JSON file.
    """
    if isinstance(navigation, list):
        # navigation is type list, resolved_navigation should also be type list
        resolved_navigation = []

        for item in navigation:
            resolved_navigation.append(_resolve_references(item, version, language))

        return resolved_navigation

    elif isinstance(navigation, dict):
        # navigation is type dict, resolved_navigation should also be type dict
        resolved_navigation = collections.OrderedDict()

        for key, value in navigation.items():
            if key == '$ref' and language in value:
                # The value is the relative path to the associated json file
                referenced_json = load_json_and_resolve_references(value[language], version, language)
                resolved_navigation = referenced_json
            else:
                resolved_navigation[key] = _resolve_references(value, version, language)

        return resolved_navigation

    else:
        # leaf node: The type of navigation should be [string, int, float, unicode]
        return navigation


def _transform_urls(version, sitemap, language):
    """
    Since paths defined in assets/sitemaps/<version>.json are defined relative to the folder structure of the content
    directories, we will need to append the URL path prefix so our URL router knows how to resolve the URLs.

    ex:
    /documentation/en/getstarted/index_en.html -> /docs/<version>/documentation/en/gettingstarted/index_en.html
    /book/01.fit_a_line/index.html -> /docs/<version>/book/01.fit_a_line/index.html

    :param version:
    :param sitemap:
    :return:
    """
    all_links_cache = {}

    if sitemap:

        for _, book in sitemap.items():
            if book and 'sections' in book:
                for chapter in book['sections']:
                    all_links = []
                    chapter_link = {}
                    if 'link' in chapter:
                        chapter_link = chapter['link']

                        for lang, url in chapter_link.items():
                            chapter_link[lang] = url_helper.append_prefix_to_path(version, chapter_link[lang])
                            all_links.append(chapter_link[lang])

                    if 'sections' in chapter:
                        for section in chapter['sections']:
                            if 'link' in section:
                                link = section['link']
                                for lang, url in link.items():
                                    link[lang] = url_helper.append_prefix_to_path(version, link[lang])
                                    all_links.append(link[lang])
                                    if not lang in chapter_link:
                                        chapter_link[lang] = link[lang]

                            if 'sections' in section:
                                all_sub_section_links = []
                                for subsection in section['sections']:
                                    if 'link' in subsection:
                                        link = subsection['link']
                                        for lang, url in link.items():
                                            link[lang] = url_helper.append_prefix_to_path(version, link[lang])
                                            all_links.append(link[lang])
                                            all_sub_section_links.append(link[lang])
                                            if not lang in chapter_link:
                                                chapter_link[lang] = link[lang]

                                section['links'] = all_sub_section_links

                    chapter['links'] = all_links
                    chapter['link'] = chapter_link

                    # Prepare link cache for language switching
                    for path in all_links:
                        key = url_helper.link_cache_key(path)
                        all_links_cache[key] = path

    # Don't expire all_links_cache. It is possible that the sitemap is loaded from saved file and bypass the generator.
    cache.set(get_all_links_cache_key(version, language), all_links_cache, None)


def get_content_navigation(content_id, version, language):
    """
    Get the navigation sitemap for a particular content service.
    """
    root_nav = get_sitemap(version, language)
    return root_nav.get(content_id, None)


def get_doc_subpath(version):
    return 'docs/%s/' % version


def _get_sitemap_path(version, language):
    """
    Give a new temporarily sitemap path.
    """
    return '%s/sitemap.%s.%s.json' % (tempfile.gettempdir(), version, language)


def get_available_versions():
    """
    Go through all the generated folders inside the parent content directory's
    versioned `docs` dir, and return a list of the first-level of subdirectories.
    """
    path = '%s/docs' % settings.EXTERNAL_TEMPLATE_DIR
    for root, dirs, files in os.walk(path):
        if root == path:
            return dirs


def get_all_links_cache_key(version, lang):
    return 'links.%s.%s' % (version, lang)


def get_external_file_path(sub_path):
    return '%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, sub_path)
