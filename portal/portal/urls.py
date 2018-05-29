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
    url(r'^(?P<path>.*)\.(?P<extension>((?!(htm|html|/)).)+)$', views.static_file_handler),

    # ---------------
    # HOME PAGE URLS
    # ---------------
    url(r'^$', views.home_root, name='home'),
    url(r'^index.cn.html', views.cn_home_root, name='cn_home'),

    # ---------------
    # BLOG URLS
    # ---------------
    # NOTE: Temporary remove the links to Blog. Wait until we have more contents.
    # url(r'^%s$' % url_helper.BLOG_ROOT, views.blog_root, name=url_helper.URL_NAME_BLOG_ROOT),
    # url(r'^%s(?P<path>.+html)$' % url_helper.BLOG_ROOT, views.blog_sub_path),

    # -------------------
    # OTHER ARBITRARY URLS
    # -------------------
    url(r'^docs/(?P<version>.*)/other/(?P<path>.*)$', views.other_path, name=url_helper.URL_NAME_OTHER),
    url(r'^docs/(?P<version>.*)/flush$', views.flush_other_page, name='flush_other_page'),
    url(r'^book$', views.book_home, name=url_helper.URL_NAME_BOOK_ROOT),
    url(r'^about_en.html', views.about_en, name='about_en'),
    url(r'^about_cn.html', views.about_cn, name='about_cn'),

    # ---------------
    # CONTENT URLS
    # ---------------
    url(r'^documentation$', views.documentation_home, name='documentation'),
    # url(r'^api$', views.api_home, name='api'),
    url(r'^book$', views.book_home, name='book'),
    # url(r'^models$', views.models_home, name='models'),
    # url(r'^mobile$', views.mobile_home, name='mobile'),

    url(r'^(?P<path>.*)$', views.content_sub_path, name='content'),

    url(r'^docs/(?P<version>[^/]+)/(?P<path>[^./]+)/?$', views.content_root_path, name=url_helper.URL_NAME_CONTENT_ROOT),
    url(r'^docs/(?P<version>[^/]+)/(?P<path>.*)$', views.content_sub_path, name=url_helper.URL_NAME_CONTENT),

    # ---------------
    # ACTION URLS
    # ---------------
    url(r'^change-version$', views.change_version, name='set_version'),
    url(r'^change-lang$', views.change_lang, name='change_lang'),
    url(r'^reload-docs$', views.reload_docs, name='reload_docs'),
    url(r'^download_latest_doc_workspace$', views.download_latest_doc_workspace, name='download_latest_doc_workspace'),
]
