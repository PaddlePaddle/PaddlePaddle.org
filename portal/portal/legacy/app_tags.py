from django import template

register = template.Library()

@register.assignment_tag(takes_context=False)
def get_dict_item(dictionary, key):
    return dictionary.get(key)


@register.assignment_tag(takes_context=True)
def first_book_url_assignment(context, book, content_id):
    # Finds the first url in the book in the default category
    if book and 'default-category' in book:
        category = book['default-category']

        if content_id == portal_helper.Content.DOCUMENTATION or \
           content_id == portal_helper.Content.API:
            # For Documentation or API, we also filter by category
            api_category = context.get('CURRENT_API_VERSION', None)
            if api_category:
                category = api_category

        leaf_node = book['categories'][category]
        if ('link' in leaf_node):
            return translation(context, leaf_node['link'])

    return ''
