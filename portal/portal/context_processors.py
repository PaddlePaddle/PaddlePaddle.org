from django.conf import settings

from portal import portal_helper


def base_context(request):
    return {
        'DEFAULT_DOCS_VERSION': settings.DEFAULT_DOC_VERSION,
        'CURRENT_DOCS_VERSION': portal_helper.get_preferred_version(request)
    }
