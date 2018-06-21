import json
import os
import re
import codecs

from bs4 import BeautifulSoup
from django.template import Template, Context
import markdown

from deploy.utils import reserve_formulas, MARKDOWN_EXTENSIONS


OPERATOR_TEMPLATE = '<div class="section" id="{{ type }}">' + (
        '<h2>{{ type }}</h2>') + (
        '<dl class="function"><dd>{{ comment|safe }}') + (
            '<table class="docutils field-list">') + (
                '<colgroup><col class="field-name"><col class="field-body"></colgroup>') + (
                '<tbody valign="top">') + (
                    '<tr class="field-odd field">') + (
                        '<th class="field-name">Inputs:</th>') + (
                        '<td class="field-body"><ul class="first simple">{% for input in inputs %}<li><strong>{{ input.name }}</strong> {% if input.duplicable == 1 %}(<em>Duplicable</em>) {% endif %}{% if input.intermediate == 1 %}(<em>Intermediate</em>) {% endif %}: {{ input.comment }}</li>{% endfor %}</ul></td>') + (
                    '</tr>') + (
                    '<tr class="field-even field"><th class="field-name">Outputs:</th>') + (
                        '<td class="field-body"><ul class="first simple">{% for output in outputs %}<li><strong>{{ output.name }}</strong> {% if output.duplicable == 1 %}(<em>Duplicable</em>) {% endif %}{% if output.intermediate == 1 %}(<em>Intermediate</em>) {% endif %}: {{ output.comment }}</li>{% endfor %}</ul></td>') + (
                    '</tr>') + (
                    '{% if attrs|length_is:"0" %}{% else %}<tr class="field-odd field"><th class="field-name">Attributes:</th>') + (
                        '<td class="field-body"><ul class="first simple">{% for attr in attrs %}<li><strong>{{ attr.name }}</strong> (<em>Duplicable</em>){% if attr.generated == 1 %} (<em>Generated</em>) {% endif %}: {{ attr.comment }}</li>{% endfor %}</ul></td>') + (
                    '</tr>{% endif %}') + (
                '</tbody>') + (
            '</table></dd>') + (
        '</dl>') + (
    '</div>')


OPERATORS_WRAPPER = (
    '<div class="document">{% verbatim %}<h1>Operators</h1><div class="section" id="operators">',
    '</div>{% endverbatim %}</div>'
)

OPERATORS_JSON_PATH_TEMPLATE = '%s/en/html/operators.json'


def generate_operators_docs_with_generated_doc_dir(generated_docs_dir, output_dir_name):
    try:
        operators_json_path = OPERATORS_JSON_PATH_TEMPLATE % (generated_docs_dir)
        if not os.path.exists(operators_json_path):
            raise Exception('operators.json does not exists in %s' % operators_json_path)

        generate_operators_page_with_path(operators_json_path, generated_docs_dir)
    except Exception, e:
        print 'Failed to build operator docs because: ', e



def generate_operators_page_with_path(operators_api_path, destination_dir):
    try:
        # Open the operators API file.
        with open(operators_api_path) as raw_operators_api_file:
            raw_operators_api = raw_operators_api_file.read()
            generate_operators_page(raw_operators_api, destination_dir, ['en/html', 'cn/html'])
    except Exception, e:
        print 'Failed to build operator docs because: ', e


def generate_operators_page(raw_operators_api, destination_dir, lang_dirs):
    operators_output = ''

    try:
        operators = clean_json_string(raw_operators_api)

        # Go through all the operators and construct a new HTML object.
        operator_template = Template(OPERATOR_TEMPLATE)

        operators_output += OPERATORS_WRAPPER[0]

        for operator in operators:
            if 'comment' in operator:

                formula_map = {}
                comment = reserve_formulas(operator['comment'], formula_map,
                                           only_reserve_double_dollar=True)

                comment = markdown.markdown(comment,
                    extensions=MARKDOWN_EXTENSIONS)

                #if len(operator_comment_line) > 0:
                if 'markdown-equation' in comment:
                    soup = BeautifulSoup('<p>' + comment + '</p>', 'lxml')
                    markdown_equation_placeholders = soup.select('.markdown-equation')

                    for equation in markdown_equation_placeholders:
                        equation.string = formula_map[equation.get('id')]

                    comment = unicode(
                        str(soup.select('body')[0])[6:-7], 'utf-8'
                    )

                operator['comment'] = comment

            operators_output += operator_template.render(Context(operator))

        operators_output += OPERATORS_WRAPPER[1]

        for lang in lang_dirs:
            operators_output_path = '%s/%s/operators.html' % (destination_dir, lang)

            print 'Saving operators.html to %s' % operators_output_path
            if not os.path.exists(os.path.dirname(operators_output_path)):
                os.makedirs(os.path.dirname(operators_output_path))

            with codecs.open(operators_output_path, 'w', 'utf-8') as operators_output_file:
                operators_output_file.write(operators_output)

    except Exception, e:
        print 'Failed to build operator docs because: ', e


def clean_json_string(body):
    """
    Takes in a string meant to be interpreted as a JSON object, and removes
    faulty characters, recursively.
    """
    try:
        return json.loads(body)

    except ValueError, e:
        if str(e).startswith('Invalid control character'):
            faulty_character_index = int(re.search(
                'char (?P<column>\d+)', str(e)).group('column'))

            return clean_json_string(
                body[:faulty_character_index] + body[faulty_character_index+1:])
