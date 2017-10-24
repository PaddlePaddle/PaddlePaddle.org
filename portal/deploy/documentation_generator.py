import os
import shutil
import codecs
from subprocess import call

from django.conf import settings
import markdown

def generate_paddle_docs(original_documentation_dir, output_dir_name):
    # Remove old generated docs directory
    destination_dir = _get_destination_documentation_dir(output_dir_name)
    if os.path.exists(destination_dir) and os.path.isdir(destination_dir):
        shutil.rmtree(destination_dir)

    if os.path.exists(os.path.dirname(original_documentation_dir)):
        destination_dir = _get_destination_documentation_dir(output_dir_name)
        settings_path = settings.PROJECT_ROOT
        script_path = settings_path + '/../../scripts/deploy/generate_paddle_docs.sh'

        if os.path.exists(os.path.dirname(script_path)):
            call([script_path, original_documentation_dir, destination_dir])
            return destination_dir
        else:
            raise Exception('Cannot find script located at %s.' % script_path)
    else:
        raise Exception('Cannot generate documentation, directory %s does not exists.' % original_documentation_dir)


def generate_models_docs(original_documentation_dir, output_dir_name):
    """
    Strip out the static and extract the body contents, headers, and body.
    """
    # Traverse through all the HTML pages of the dir, and take contents in the "markdown" section
    # and transform them using a markdown library.
    destination_documentation_dir = _get_destination_documentation_dir(output_dir_name)

    for subdir, dirs, all_files in os.walk(original_documentation_dir):
        for file in all_files:
            subpath = os.path.join(subdir, file)[len(
                original_documentation_dir):]

            # Replace .md with .html.
            (name, extension) = os.path.splitext(subpath)
            if extension == '.md':
                subpath = name + '.html'

            new_path = '%s/%s' % (destination_documentation_dir, subpath)

            if '.md' in file or 'images' in subpath:
                if not os.path.exists(os.path.dirname(new_path)):
                    os.makedirs(os.path.dirname(new_path))

            if '.md' in file:
                # Convert the contents of the MD file.
                with open(os.path.join(subdir, file)) as original_md_file:
                    markdown_body = original_md_file.read()

                    with codecs.open(new_path, 'w', 'utf-8') as new_html_partial:
                        # Strip out the wrapping HTML
                        new_html_partial.write(
                            '{% verbatim %}\n' + markdown.markdown(
                                unicode(markdown_body, 'utf-8'),
                                extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables']
                            ) + '\n{% endverbatim %}'
                        )

            elif 'images' in subpath:
                shutil.copyfile(os.path.join(subdir, file), new_path)

    return destination_documentation_dir


def generate_book_docs(original_documentation_dir, output_dir_name):
    # Remove old generated docs directory
    destination_dir = _get_destination_documentation_dir(output_dir_name)
    if os.path.exists(destination_dir) and os.path.isdir(destination_dir):
        shutil.rmtree(destination_dir)

    if os.path.exists(os.path.dirname(original_documentation_dir)):
        destination_dir = _get_destination_documentation_dir(output_dir_name)
        settings_path = settings.PROJECT_ROOT
        script_path = settings_path + '/../../scripts/deploy/generate_book_docs.sh'

        if os.path.exists(os.path.dirname(script_path)):
            call([script_path, original_documentation_dir, destination_dir])
            return destination_dir
        else:
            raise Exception('Cannot find script located at %s.' % script_path)
    else:
        raise Exception('Cannot generate documentation, directory %s does not exists.' % original_documentation_dir)


def _get_destination_documentation_dir(output_dir_name):
    return '%s/%s' % (settings.GENERATED_DOCS_DIR, output_dir_name)