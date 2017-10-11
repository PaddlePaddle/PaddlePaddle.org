from django.conf import settings

from portal import portal_helper
from portal import url_helper


def base_context(request):
    return {
        'CURRENT_DOCS_VERSION': portal_helper.get_preferred_version(request),
        'settings': settings,
        'url_helper': url_helper
    }
