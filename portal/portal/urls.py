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

    # ---------------
    # BLOG URLS
    # ---------------
    url(r'^%s$' % url_helper.BLOG_ROOT, views.blog_root, name=url_helper.URL_NAME_BLOG_ROOT),
    url(r'^%s(?P<path>.+html)$' % url_helper.BLOG_ROOT, views.blog_sub_path),

    # ---------------
    # TUTORIAL URLS
    # ---------------
    url(r'^tutorial/(?P<version>.*)/$', views.tutorial_root, name=url_helper.URL_NAME_TUTORIAL_ROOT),
    url(r'^docs/(?P<version>.*)/%s(?P<path>.*)$' % url_helper.BOOK_ROOT, views.book_sub_path, name=url_helper.URL_NAME_TUTORIAL),

    # -------------------
    # DOCUMENTATION URLS
    # -------------------
    url(r'^docs/(?P<version>.*)/$', views.documentation_root, name=url_helper.URL_NAME_DOCS_ROOT),
    url(r'^docs/(?P<version>.*)/%s(?P<path>.*)$' % url_helper.DOCUMENTATION_ROOT, views.documentation_path, name=url_helper.URL_NAME_DOCS),

    # ---------------
    # MODELS URLS
    # ---------------
    url(r'^docs/(?P<version>.*)/%s(?P<path>.*)$' % url_helper.MODEL_ROOT, views.models_path, name=url_helper.URL_NAME_MODEL),

    # ---------------
    # ACTION URLS
    # ---------------
    url(r'^change-version$', views.change_version, name='set_version'),
    url(r'^change-lang$', views.change_lang, name='change_lang')
]

