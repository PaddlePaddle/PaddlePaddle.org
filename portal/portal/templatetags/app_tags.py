from django import template


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

@register.inclusion_tag('_content_links.html', takes_context=True)
def content_links(context, book_id):
    #TODO[thuan]: Load content links for book with id

    return {
        'request': context.request,
        'side_nav_content': TUTORIAL_NAV_DATA
    }
