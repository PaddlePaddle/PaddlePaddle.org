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

"""portal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
import views

from portal import url_helper


urlpatterns = [
    # ---------------------
    # STATIC FILE HANDLERS
    # ---------------------
    url(r'^documentation/(?P<path>.*)\.(?P<extension>((?!(htm|html|/)).)+)$', views.static_file_handler),

    # ---------------
    # HOME PAGE URLS
    # ---------------
    url(r'^$', views.home_root, name='home'),
    url(r'^zh', views.zh_home_root, name='zh_home'),
    url(r'^en', views.en_home_root, name='en_home'),

    url(r'^suite', views.suite_root, name='suite'),
    # url(r'^huangpu', views.huangpu_root, name='huangpu'),

    # ---------------
    # BLOG URLS
    # ---------------
    # NOTE: Temporary remove the links to Blog. Wait until we have more contents.
    # url(r'^%s$' % url_helper.BLOG_ROOT, views.blog_root, name=url_helper.URL_NAME_BLOG_ROOT),
    # url(r'^%s(?P<path>.+html)$' % url_helper.BLOG_ROOT, views.blog_sub_path),

    # -------------------
    # OTHER ARBITRARY URLS
    # -------------------
    url(r'^about_en.html', views.about_en, name='about_en'),
    url(r'^about_cn.html', views.about_cn, name='about_cn'),
    url(r'^404.html', views.not_found, name='not_found'),
    url(r'^contact', views.contact, name='contact'),

    # ---------------
    # ACTION URLS
    # ---------------
    url(r'^change-version$', views.change_version, name='set_version'),
    url(r'^change-lang$', views.change_lang, name='change_lang'),
    url(r'^reload-docs$', views.reload_docs, name='reload_docs'),
    url(r'^get-menu$', views.get_menu, name='get_menu'),
    url(r'^save-menu$', views.save_menu, name='save_menu'),
    url(r'^download$', views.tracked_download, name='tracked_download'),


    # ---------------
    # CONTENT URLS
    # ---------------
    # NOTE: This was the old way, with every content site having its own home.
    url(r'^documentation/zh/?((?!/).)*$', views.content_home_zh, name='documentationz'),
    url(r'^documentation/en/?((?!/).)*$', views.content_home_en, name='documentatione'),
    url(r'^documentation/?((?!/).)*$', views.content_home, name='documentation'),
    # url(r'^documentation$', views.content_home, name='documentation'),
    # Old content url format.
    url(r'^docs/(?P<version>(?!/).*)/documentation/(?P<is_fluid>fluid/)?(?P<lang>zh|en)/(?P<path>.*)$', views.old_content_link,
        name='old_content_link'),
    url(r'^search$', views.search, name='search'),


    # HAS TO BE KEPT IN THE END, because it picks everything.
    url(r'^(?P<path>.*)$', views.content_sub_path, name='content'),
]
