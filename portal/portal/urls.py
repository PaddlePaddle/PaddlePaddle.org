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
from django.conf.urls.i18n import i18n_patterns
import views

# def staticfiles_urlpatterns(prefix=None):
#     """
#     Helper function to return a URL pattern for serving static files.
#     """
#     # if prefix is None:
#     #     prefix = settings.STATIC_URL
#     return static(None, view=views.css_handler)

urlpatterns = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^(?P<path>.*)\.(?P<extension>((?!(htm|html)).)+)$', views.static_file_handler),
    url(r'^$', views.home_root, name='home'),
    url(r'^blog/$', views.blog_root, name='blog_root'),
    url(r'^blog/(?P<path>.+html)$', views.blog_sub_path),
    url(r'^tutorial/$', views.tutorial_root, name='tutorial_root'),
    url(r'^docs/(?P<version>.*)/book/(?P<path>.*)$', views.book_sub_path),
    url(r'^docs/(?P<version>.*)/documentation/(?P<language>.*)/html/$', views.documentation_root),
    url(r'^docs/(?P<version>.*)/documentation/(?P<language>.*)/html/(?P<path>.*)$', views.documentation_sub_path),
    url(r'^models/(?P<version>.*)/$', views.models_root),
    url(r'^change-version$', views.change_version, name='set_version'),
    url(r'^change-lang$', views.change_lang, name='change_lang')
]

