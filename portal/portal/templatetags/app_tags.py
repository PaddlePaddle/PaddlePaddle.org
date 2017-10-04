# -*- coding: utf-8 -*-
from django import template
from portal import sitemap_helper
from django.conf import settings

# TODO[Thuan]: Move to external file
TUTORIAL_NAV_DATA = {
    "title": "Tutorial",
    "chapters": [
        {
            "title": "Getting Started",
            "sections": [
                {
                    "title": "Overview",
                    "link": "/documentation/develop/en/html/getstarted/index_en.html"
                },
                {
                    "title": "Installation",
                    "link": "/documentation/develop/en/html/getstarted/build_and_install/index_en.html"
                },
                {
                    "title": "What's New",
                    "link": "/tutorial"
                }
            ]
        },
        {
            "title": "Applications of Deep Learning",
            "sections": [
                {
                    "title": "Linear Regression",
                    "link": "/book/01.fit_a_line/index.html"
                },
                {
                    "title": "Recognize Digits",
                    "link": "/book/02.recognize_digits/index.html"
                },
                {
                    "title": "Image Classification",
                    "link": "/book/03.image_classification/index.html"
                },
                {
                    "title": "Word2Vec",
                    "link": "/book/04.word2vec/index.html"
                },
                {
                    "title": "Personalized Recommendation",
                    "link": "/book/05.recommender_system/index.html"
                },
                {
                    "title": "Sentiment Analysis",
                    "link": "/book/06.understand_sentiment/index.html"
                },
                {
                    "title": "Semantic Role Labelingn",
                    "link": "/book/07.label_semantic_roles/index.html"
                },
                {
                    "title": "Machine Translation",
                    "link": "/book/08.machine_translation/index.html"
                }
            ]
        },
        {
            "title": "Advanced",
            "sections": [
                {
                    "title": "Distributed Training on AWS with Kubernetes",
                    "link": "/documentation/develop/en/html/howto/usage/k8s/k8s_en.html"
                },
                {
                    "title": "Tune GPU Performance",
                    "link": "/documentation/develop/en/html/howto/optimization/gpu_profiling_en.html"
                }
            ]
        },
    ]
}

register = template.Library()


@register.filter(name='links')
def links(chapter):
    return map(lambda s: s['link'], chapter['sections'])


@register.simple_tag(takes_context=True)
def apply_class_if_template(context, template_file_name, class_name):
    '''
    Function that returns 'active' if the current base template matches the passed in template name, otherwise return
    empty string.  This method is used to apply the "active" class to the root navigation links
    :param context:
    :param template_file_name:
    :return:
    '''
    if context.template.name == template_file_name:
        return class_name
    else:
        return ''

@register.inclusion_tag('_nav_bar.html', takes_context=True)
def nav_bar(context):
    root_navigation = sitemap_helper.get_sitemap(
        sitemap_helper.get_preferred_version(context.request)
    )

    current_lang_code = context.request.LANGUAGE_CODE

    # Since we default to english, we set the change lang toggle to chinese
    lang_label = u"中文"
    lang_link = '/change-lang?lang_code=zh'

    if current_lang_code and current_lang_code == "zh":
        lang_label = "English"
        lang_link = '/change-lang?lang_code=en'

    return {
        'request': context.request,
        'template': context.template,
        'root_nav': root_navigation,
        'lang_def': { 'label': lang_label, 'link': lang_link },
        'doc_mode': settings.DOC_MODE
    }

@register.inclusion_tag('_content_links.html', takes_context=True)
def content_links(context, book_id):
    tutorial_nav_data = sitemap_helper.get_book_navigation(
        book_id,
        sitemap_helper.get_preferred_version(context.request)
    )
    return {
        'request': context.request,
        'side_nav_content': tutorial_nav_data
    }

@register.inclusion_tag('_version_links.html', takes_context=True)
def version_links(context, book_id):
    versions = sitemap_helper.get_available_versions()
    preferred_version = sitemap_helper.get_preferred_version(context.request)

    is_hidden = True
    if context.template and (context.template.name == 'tutorial.html' or context.template.name == 'documentation.html'):
        is_hidden = False

    return {
        'request': context.request,
        'version_list': versions,
        'current_version': preferred_version,
        'is_hidden': is_hidden
    }

