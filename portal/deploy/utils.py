import re


MARKDOWN_EXTENSIONS = [
    'markdown.extensions.fenced_code',
    'markdown.extensions.tables',
    'pymdownx.superfences',
    'pymdownx.escapeall'
]

def reserve_formulas(markdown_body, formula_map, only_reserve_double_dollar=False):
    """
    Store the math formulas to formula_map before markdown conversion
    """
    place_holder = '<span class="markdown-equation" id="equation-%s"></span>'
    if only_reserve_double_dollar:
        m = re.findall('(\$\$[^\$]+\$\$)', markdown_body)
    else:
        m = re.findall('(\$\$?[^\$]+\$?\$)', markdown_body)

    for i in xrange(len(m)):
        formula_map['equation-' + str(i)] = m[i]
        markdown_body = markdown_body.replace(m[i], place_holder % i)

    return markdown_body
