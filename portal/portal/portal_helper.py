from django.utils.translation import LANGUAGE_SESSION_KEY
from django.conf import settings


def get_preferred_version(request):
    preferred_version = settings.DEFAULT_DOCS_VERSION
    if request and 'preferred_version' in request.session:
        preferred_version = request.session['preferred_version']

    return preferred_version


def set_preferred_version(request, preferred_version):
    if request and preferred_version:
        request.session['preferred_version'] = preferred_version


def get_preferred_language(request):
    preferred_lang = request.session.get(LANGUAGE_SESSION_KEY, None)
    if not preferred_lang:
        preferred_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, "en")

    return preferred_lang


def set_preferred_language(request, response, lang):
    request.session[LANGUAGE_SESSION_KEY] = lang
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)