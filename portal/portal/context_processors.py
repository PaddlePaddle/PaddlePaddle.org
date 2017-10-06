from django.conf import settings

from portal import sitemap_helper


def base_context(request):
    return {
        'DOCS_VERSION': sitemap_helper.get_preferred_version(request)
    }
