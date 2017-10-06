from django.conf import settings

from portal import sitemap_helper


def base_context(request):
    return {
        'DEFAULT_DOCS_VERSION': settings.DEFAULT_DOC_VERSION,
        'DOCS_VERSION': sitemap_helper.get_preferred_version(request)
    }
