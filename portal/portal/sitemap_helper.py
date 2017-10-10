import json
import os

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseServerError


def get_sitemap(version):
    version = version.strip("/")
    cache_key = 'sitemap.%s' % version
    sitemap_cache = cache.get(cache_key, None)

    if not sitemap_cache:
        sitemap_cache = _load_sitemap_from_file(version)

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
            sitemap = json.loads(json_data)
        except Exception as e:
            print "Cannot load sitemap from file %s: %s" % (file_path, e.message)
    else:
        print "Cannot load sitemap from file %s" % file_path
        raise HttpResponseServerError("Cannot load sitemap from file %s" % file_path)

    return sitemap


def get_preferred_version(request):
    preferred_version = settings.DEFAULT_DOC_VERSION
    if request and 'preferred_version' in request.session:
        preferred_version = request.session['preferred_version']

    return preferred_version


def set_preferred_version(request, preferred_version):
    if request and preferred_version:
        request.session['preferred_version'] = preferred_version


def generate_sitemap(version):
    book_template_path = _get_book_path(version)
    try:
        print "Generating sitemap from %s" % book_template_path
        book_template_str = open(book_template_path).read()
        book_template = json.loads(book_template_str)

        sitemap = {}
        all_sections = _load_all_sections(version)
        for book in book_template["books"]:
            book_map = {
                "id": book["id"],
                "name": book["name"],
                "chapters": []
            }

            for chapter_id in book["chapters"]:
                chapter_ref_map = all_sections.get(chapter_id, None)

                if chapter_ref_map:
                    chapter_map = {
                        "id": chapter_id
                    }
                    chapter_map.update(chapter_ref_map)
                    book_map["chapters"].append(chapter_map)

                    if 'sections' in chapter_ref_map:
                        sections = chapter_ref_map['sections']

                        # Go through each section link and prepend a /docs/version.  This allow relative links in the
                        # corresponding site.json to be mapped correctly to the local directory structure.
                        # Also set the root_url (which is the first section's link) on each book.
                        for section in sections:
                            if "link" in section:
                                section["link"] = "/%s%s" % (get_doc_subpath(version), section["link"].strip("/"))
                                if "root_url" not in book_map:
                                    book_map["root_url"] = section["link"]

            sitemap[book["id"]] = book_map

        sitemap_path = _get_sitemap_path(version)
        with open(sitemap_path, 'w') as fp:
            json.dump(sitemap, fp)

        return sitemap
    except Exception as e:
        print "Cannot generate sitemap: %s" % e
        return None


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
    return "%s/%ssitemap.json" % (settings.EXTERNAL_TEMPLATE_DIR, get_doc_subpath(version))


def _get_chapter_path(version, module):
    return "%s/%s%s/site.json" % (settings.EXTERNAL_TEMPLATE_DIR, get_doc_subpath(version), module)


def get_available_versions():
    path = '%s/docs' % settings.EXTERNAL_TEMPLATE_DIR
    for root, dirs, files in os.walk(path):
        if root == path:
            return dirs
