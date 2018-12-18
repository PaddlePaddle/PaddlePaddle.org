# -*- coding: utf-8 -*-
#   Copyright (c) 2018 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import posixpath
import urllib
from urlparse import urlparse, parse_qs
import json
import datetime
import pytz
import dateutil.parser
import ipaddress

from django.template.loader import get_template
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils.six.moves.urllib.parse import unquote
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.views import static
from django.template import TemplateDoesNotExist
from django.core.cache import cache
from django.http import JsonResponse
from django import forms
import requests
from user_agents import parse

from portal import menu_helper, portal_helper, url_helper
from deploy import transform
from portal import url_helper


def change_version(request):
    """
    Change current documentation version.
    """
    # Look for a new version in the URL get params.
    version = request.GET.get('preferred_version', settings.DEFAULT_DOCS_VERSION)

    response = redirect('/')

    path = urlparse(request.META.get('HTTP_REFERER')).path

    try:
        if not path == '/':
            response = _find_matching_equivalent_page_for(path, request, None, version)
    except:
        print("Unable to switch version properly. redirect to home page")
        content_id, lang, version = url_helper.get_parts_from_url_path(path)
        if lang == None:
            lang = 'en'

        response = redirect('/documentation/' + lang)

    return response


def change_lang(request):
    """
    Change current documentation language.
    """
    lang = request.GET.get('lang_code', 'en')

    # By default, intend to redirect to the home page.

    path = urlparse(request.META.get('HTTP_REFERER')).path

    if path == '/about_cn.html':
        response = redirect('/about_en.html')
    elif path == '/about_en.html':
        response = redirect('/about_cn.html')
    elif path.endswith('404.html'):
        portal_helper.set_preferred_language(request, None, lang)
        response = redirect('/404.html')
    elif path in ['/documentation/models', '/documentation/mobile']:
        # There is no information on lang and version. The only way is to redirect to the documentation home
        response = redirect('/documentation/%s' % lang)
    elif not path in ['/', '/en', '/zh', '/search', '/suite', '/huangpu']:
        # If not for homepage, its regular documentations.
        response = _find_matching_equivalent_page_for(path, request, lang)
    else:
        response = redirect('/%s' % lang)

    return response


def _find_matching_equivalent_page_for(path, request, lang=None, version=None):
    content_id, old_lang, old_version = url_helper.get_parts_from_url_path(
        path)

    # Try to find the page in this content's navigation.
    menu_path = menu_helper.get_menu_path_cache(
        content_id, old_lang, old_version)

    if content_id in ['book']:
        path = os.path.join(os.path.dirname(
            path), 'README.%smd' % ('' if old_lang == 'en' else 'cn.'))

    matching_link = None
    if menu_path.endswith('.json'):
        with open(menu_path, 'r') as menu_file:
            menu = json.loads(menu_file.read())
            path_to_seek = url_helper.get_raw_page_path_from_html(path)

            # HACK: If this is an API lookup, forcefully adapt to the naming
            # convention of api_cn/name_cn (and vice versa) for the paths to seek.
            # This is a result of the Chinese API introduction in v1.2
            if not old_version < '1.2' and path_to_seek[0].startswith('api/') or path_to_seek[0].startswith('api_'):
                new_path_to_seek = []

                for p2s in list(path_to_seek):
                    extensionless_path, extension = os.path.splitext(
                        p2s.replace('api/', 'api_cn/') if old_lang == 'en' else p2s.replace('api_cn/', 'api/'))
                    new_path_to_seek.append(
                        ((extensionless_path + '_cn') if old_lang == 'en' else extensionless_path[:-3]) + extension)

                path_to_seek = tuple(new_path_to_seek)

            if lang:
                # HACK: Since we failed to find a way make a merged menu.json.
                new_menu_path = menu_helper.get_menu_path_cache(
                    content_id, lang, version)

                with open(new_menu_path, 'r') as new_menu_file:
                    new_menu = json.loads(new_menu_file.read())

                    # We are switching to new language
                    matching_link = menu_helper.find_all_languages_for_link(
                        path_to_seek,
                        old_lang, new_menu['sections'], lang
                    )
                    version = old_version

            else:
                # We are switching to new version
                new_menu_path = menu_helper.get_menu_path_cache(
                    content_id, old_lang, version)

                with open(new_menu_path, 'r') as new_menu_file:
                    new_menu = json.loads(new_menu_file.read())

                    # Try to find this link in the new menu path.
                    # NOTE: We account for the first and last '/'.
                    matching_link = menu_helper.find_link_in_sections(
                        new_menu['sections'], path_to_seek)
                lang = old_lang

    if matching_link:
        content_path, url_prefix = url_helper.get_full_content_path(
            content_id, lang, version)

        # Because READMEs get replaced by index.htmls, so we have to undo that.
        if content_id in ['book'] and old_lang != lang:
            matching_link = os.path.join(os.path.dirname(
                matching_link), 'index.%shtml' % ('' if lang == 'en' else 'cn.'))

        return redirect(url_helper.get_url_path(url_prefix, matching_link))

    # If no such page is found, redirect to first link in the content.
    else:
        return _redirect_first_link_in_contents(
            request, content_id, version, lang)


def reload_docs(request):
    try:
        path = urlparse(request.META.get('HTTP_REFERER')).path

        # Get all the params from the URL and settings to generate new content.
        content_id, lang, version = url_helper.get_parts_from_url_path(
            path)
        menu_path = menu_helper.get_menu_path_cache(
            content_id, lang, version)
        content_path, url_prefix = url_helper.get_full_content_path(
            content_id, lang, version)

        # Generate new content.
        _generate_content(os.path.dirname(
            menu_path), content_path, content_id, lang, version)

        return redirect(path)

    except Exception as e:
        return HttpResponseServerError("Cannot reload docs: %s" % e)


def _redirect_first_link_in_contents(request, content_id, version=None, lang=None, is_raw=False):
    """
    Given a version and a content service, redirect to the first link in it's
    navigation.
    """
    if not lang:
        lang = portal_helper.get_preferred_language(request)

    # Get the directory paths on the filesystem, AND of the URL.
    content_path, url_prefix = url_helper.get_full_content_path(
        content_id, lang, version)

    # If the content doesn't exist yet, try generating it.
    navigation = None
    try:
        navigation, menu_path = menu_helper.get_menu(content_id, lang, version)
        assert os.path.exists(content_path)

    except Exception, e:
        if type(e) in [AssertionError, IOError]:
            if type(e) == IOError:
                menu_path = e[1]

            _generate_content(os.path.dirname(
                menu_path), content_path, content_id, lang, version)

            if not navigation:
                navigation, menu_path = menu_helper.get_menu(
                    content_id, lang, version)
        else:
            raise e

    try:
        if navigation:
            path = _get_first_link_in_contents(navigation, lang)
        else:
            path = 'README.cn.html' if lang == 'zh' else 'README.html'

        # Because READMEs get replaced by index.htmls, so we have to undo that.
        if content_id in ['book']:
            path = os.path.join(os.path.dirname(path), 'index.%shtml' % (
                '' if lang == 'en' else 'cn.'))

        if not path:
            msg = 'Cannot perform reverse lookup on link: %s' % path
            raise Exception(msg)

        return redirect(url_helper.get_url_path(url_prefix, path) + ('?raw=1' if is_raw else ''))

    except Exception as e:
        print e.message
        return redirect('/')


def _generate_content(source_dir, destination_dir, content_id, lang, version):
    # If this content has been generated yet, try generating it.
    if not os.path.exists(destination_dir):

        # Generate the directory.
        os.makedirs(destination_dir)

    transform(source_dir, destination_dir, content_id, version, lang)


def _get_first_link_in_contents(navigation, lang):
    """
    Given a content's menu, and a language choice, get the first available link.
    """
    # If there are sections in the root of the menu.
    first_chapter = None
    if navigation and 'sections' in navigation and len(navigation['sections']) > 0:
        # Gotta find the first chapter in current language.
        for section in navigation['sections']:
            if 'title' in section and lang in section['title']:
                first_chapter = section
                break

    # If there is a known root "section" with links.
    if first_chapter and 'link' in first_chapter:
        return first_chapter['link'][lang]

    # Or if there is a known root section with subsections with links.
    elif first_chapter and ('sections' in first_chapter) and len(first_chapter['sections']) > 0:
        first_section = first_chapter['sections'][0]
        return first_section['link'][lang]

    # Last option is to attempt to see if there is only one link on the title level.
    elif 'link' in navigation:
        return navigation['link'][lang]


def static_file_handler(request, path, extension, insecure=False, **kwargs):
    """
    Note: This is static handler is only used during development.
    In production, the Docker image uses NGINX to serve static content.

    Serve static files below a given point in the directory structure or
    from locations inferred from the staticfiles finders.
    To use, put a URL pattern such as::
        from django.contrib.staticfiles import views
        url(r'^(?P<path>.*)$', views.serve)
    in your URLconf.
    It uses the django.views.static.serve() view to serve the found files.
    """
    append_path = ''

    if not settings.DEBUG and not insecure:
        raise Http404

    normalized_path = posixpath.normpath(unquote(path)).lstrip('/')

    absolute_path = settings.WORKSPACE_DIR + '/' + append_path + normalized_path + '.' + extension
    if not absolute_path:
        if path.endswith('/') or path == '':
            raise Http404('Directory indexes are not allowed here.')

        raise Http404('\'%s\' could not be found' % path)

    document_root, path = os.path.split(absolute_path)
    return static.serve(request, path, document_root=document_root, **kwargs)


def get_menu(request):
    if not settings.DEBUG:
        return HttpResponseServerError(
            'You need to be in a local development environment to show the raw menu')

    path = urlparse(request.META.get('HTTP_REFERER')).path

    content_id, lang, version = url_helper.get_parts_from_url_path(
        path)

    navigation, menu_path = menu_helper.get_menu(
        content_id, lang, version)

    return HttpResponse(json.dumps(navigation), content_type='application/json')


def save_menu(request):
    try:
        assert settings.DEBUG
        menu = json.loads(request.POST.get('menu'), None)
    except:
        return HttpResponseServerError('You didn\'t submit a valid menu')

    # Write the new menu to disk.
    path = urlparse(request.META.get('HTTP_REFERER')).path

    content_id, lang, version = url_helper.get_parts_from_url_path(
        path)
    menu_path = menu_helper.get_menu_path_cache(
        content_id, lang, version)

    with open(menu_path, 'w') as menu_file:
        menu_file.write(json.dumps(menu, indent=4))

    return HttpResponse(status='200')


######## Paths and content roots below ########################

def _get_static_content_from_template(path):
    """
    Search the path and render the content
    Return "Page not found" if the template is missing.
    """
    try:
        static_content_template = get_template(path)
        return static_content_template.render()

    except TemplateDoesNotExist:
        return None

def home_root(request):
    return render(request, 'index.html')


def en_home_root(request):
    portal_helper.set_preferred_language(request, None, 'en')
    return render(request, 'index.html')


def zh_home_root(request):
    portal_helper.set_preferred_language(request, None, 'zh')
    return render(request, 'index.html')


def suite_root(request):
    portal_helper.set_preferred_language(request, None, 'zh')
    return render(request, 'pps.html')


def huangpu_root(request):
    portal_helper.set_preferred_language(request, None, 'zh')

    is_mobile = parse(request.META.get('HTTP_USER_AGENT', '')).is_mobile

    return render(
        request,
        'huangpu-mobile.html' if is_mobile else 'huangpu.html',
        {
            'title': '黄埔计划延展图',
            'wrapper_class': 'huangpu-mobile' if is_mobile else None
        }
    )


def about_en(request):
    portal_helper.set_preferred_language(request, None, 'en')
    return render(request, 'about_en.html')


def about_cn(request):
    portal_helper.set_preferred_language(request, None, 'zh')
    return render(request, 'about_cn.html')


def not_found(request):
    return render(request, '404.html')


def content_home_zh(request, content_id):
    return content_home(request, None, 'zh')


def content_home_en(request, content_id):
    return content_home(request, None, 'en')


def content_home(request, content_id, lang=None):
    is_raw = request.GET.get('raw', None) == '1'

    if lang == None:
        lang = portal_helper.get_preferred_language(request)

    content_id = urlparse(request.path).path[15:]

    if hasattr(request, 'urlconf') and request.urlconf == 'visualDL.urls':
        content_id = 'visualdl'
    elif content_id in ['en', 'zh']:
        # If content_id is en or zh, it means we are dealing with regular documentations
        content_id = 'docs'
    # else content_id stays the same, it could be models or mobile

    return _redirect_first_link_in_contents(
        request, content_id,
        'develop' if content_id == 'visualdl' else portal_helper.get_preferred_version(request),
        lang, is_raw
    )


def content_sub_path(request, path=None):
    """
    This is the primary function that renders all static content (.html) pages.
    It builds the context and passes it to the only documentation template rendering template.
    """
    is_raw = request.GET.get('raw', None)
    static_content = _get_static_content_from_template(path)

    if static_content:
        # Because this is the best metadata we have on if this is VDL or not.
        is_visualdl = hasattr(
            request, 'urlconf') and request.urlconf == 'visualDL.urls'

        if is_raw and is_raw == '1':
            response = HttpResponse(static_content, content_type="text/html")
            return response
        else:
            response = render(request, '%scontent_panel.html' % ('visualdl/' if is_visualdl else ''), {
                'static_content': static_content
            })
            return response

    raise Http404


def old_content_link(request, version=None, is_fluid=None, lang=None, path=None):
    """
    This function handles the URL from the previous version.
    If the version is available, it will redirect to the latest URL format and
    let the current system to load the content.

    If the version is not available, it raises Http404 error
    """
    allowed_version = settings.VERSIONS
    if version not in map(lambda x: x['name'], allowed_version):
        raise Http404

    else:
        if not is_fluid  and version not in ['0.10.0', '0.11.0', '0.12.0']:
            version = '0.12.0'
        elif is_fluid and version not in ['0.13.0', '0.14.0']:
            # Version 0.13.0 and 0.14.0 are the only two versions we should support.
            # We expect no one to bookmark/share 0.15.0 link with old URL pattern.
            version = '0.14.0'

        latest_path = '/documentation/docs/%s/%s/%s' % (lang, version, path)
        return redirect(latest_path)


def search(request):
    """
    Placeholder for a search results page that uses local indexes.
    """
    lang = request.GET.get('language', '')
    portal_helper.set_preferred_language(request, None, lang)

    return render(request, 'search.html', {
        'q': request.GET.get('q', ''),
        'lang': lang,
        'CURRENT_DOCS_VERSION': request.GET.get('version', ''),
    })


def contact(request):
    is_personal = request.POST.get('isPersonal', None) == 'true'
    organization = request.POST.get('organization', None)
    name = request.POST.get('name', None)
    phone = request.POST.get('phone', None)
    email = request.POST.get('email', None)
    reason = request.POST.get('reason', None)

    # Datetime in Beijing time.
    beijing_timezone = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now(beijing_timezone)

    # Authenticated POST.
    requests.post(settings.AIRTABLE_CONTACT_URL, headers = {
        'Authorization': 'Bearer ' + settings.AIRTABLE_API_KEY,
        'Content-type': 'application/json'
    }, data = json.dumps({
        'fields': {
            '发送日期': now.isoformat(),
            '身份类型': '个人' if is_personal else '企业',
            '企业名称': organization,
            '联系人': name,
            '手机号码': phone,
            '电子邮件': email,
            '咨询内容': reason
        }
    }))

    return JsonResponse({})


def tracked_download(request):
    url = request.GET.get('url', None)

    if not url:
        raise Http404

    acceptable_sources = ['paddlepaddle.org', 'wiki.baidu.com', 'github.com']
    acceptable_extension = '.whl'

    # Make sure that the referer is either PaddlePaddle.org or wiki.baidu.com or github.
    referer = request.META.get('HTTP_REFERER', None)

    if referer:
        referer = urlparse(referer)

        if referer.netloc not in acceptable_sources or not url.endswith(
            acceptable_extension):
            raise Http404

        # [Roughly] Determine if the IP of this request is within Baidu, internally.
        remote_ip = get_client_ip(request)
        is_internal_ip = ip_in_internal_range(unicode(remote_ip))

        # Fetch the newest data on downloads, for the current date.
        last_record = requests.get(settings.AIRTABLE_WHEEL_DOWNLOADS + (
            '?maxRecords=1&view=Grid%20view&sort%5B0%5D%5Bfield%5D=Date&sort%5B0%5D%5Bdirection%5D=desc'), headers = {
            'Authorization': 'Bearer ' + settings.AIRTABLE_API_KEY
        }).json()['records'][0]

        beijing_timezone = pytz.timezone('Asia/Shanghai')
        last_date = dateutil.parser.parse(last_record['fields']['Date']).replace(
            tzinfo=beijing_timezone)

        today = datetime.datetime.now(beijing_timezone)
        today.replace(hour=0, minute=0, second=0)

        zh_internal = ' (公司内部用户)'.decode('utf-8')
        target_field = referer.netloc + (zh_internal if is_internal_ip else '')

        # Increment or decrement the counter for the referer field.
        # Either create a new record or update an existing one based on whether
        # one has been created or not.
        if last_date.year == today.year and last_date.month == today.month and last_date.day == today.day:
            requests.patch(settings.AIRTABLE_WHEEL_DOWNLOADS + '/' + last_record['id'], headers = {
                'Authorization': 'Bearer ' + settings.AIRTABLE_API_KEY,
                'Content-type': 'application/json'
            }, data = json.dumps({
                'fields': {
                    target_field: last_record['fields'][target_field] + 1
                }
            }))

        else:
            fields = {
                'Date': today.strftime('%Y-%m-%d')
            }

            acceptable_sources_fields = acceptable_sources + (
                [source + zh_internal for source in acceptable_sources])

            for acceptable_source_field in acceptable_sources_fields:
                fields[acceptable_source_field] = 1 if target_field == acceptable_source_field else 0

            requests.post(settings.AIRTABLE_WHEEL_DOWNLOADS, headers = {
                'Authorization': 'Bearer ' + settings.AIRTABLE_API_KEY,
                'Content-type': 'application/json'
            }, data = json.dumps({
                'fields': fields
            }))

    else:
        # NOTE: We allow this to pass.
        # We do not complain about this because it allows people to copy and
        # paste URLs, which should be a supported web practice.
        pass

    return redirect(url)


# Adopted from https://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
# and tested against current server setup.
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


"""
Finds out if a given IP is in a range of IPs (which are pre-loaded in settings)
"""
def ip_in_internal_range(ip_to_check):
    networks_with_masks = settings.INTERNAL_RANGE_IPS.split(',')
    ip_address = ipaddress.ip_address(ip_to_check)

    for network_with_mask in networks_with_masks:
        network_with_mask_pieces = network_with_mask.split(':')
        if ip_address in ipaddress.ip_network(
            unicode(network_with_mask_pieces[0] + '/' + network_with_mask_pieces[2]), strict=False):
            return True

    return False
