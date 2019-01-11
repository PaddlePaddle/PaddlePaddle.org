import os
import re
import json
import math
from subprocess import check_output
import tempfile

import jieba
from bs4 import BeautifulSoup
from textblob import TextBlob as tb
from django.conf import settings
from django.core.management import BaseCommand

from .utils import sanitize_version


def get_section_for_api_title(title, depth=0):
    """
    Traverses the tree upwards from the title node upto 3 levels in search for
    a "section" classed 'div'. If it finds it, returns it.
    """
    for parent in title.parents:
        if parent and parent.has_attr('class') and 'section' in parent['class']:
            return parent
        else:
            if depth == 2:
                return None

            return get_section_for_api_title(parent, depth+1)

    return None


def jieba_zh_title(raw_title):
    segments = jieba.cut_for_search(raw_title)
    joined_segments = ''

    for segment in segments:
        if len(segment.strip()):
            joined_segments += ' ' + segment

    return joined_segments.strip()


def jieba_zh_content(token):
    chinese_seg_list = [' '.join(jieba.cut_for_search(s)) for s in token]
    return ', '.join(chinese_seg_list)


"""
Primarily done to reduce index size, may be reversed in future.
"""
def filter_insignificant_tokens(stripped_strings):
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    # Reserving them for the API.
    special_characters = ['=', '/', '_', '.']

    filtered_string = ''

    for stripped_string in stripped_strings:
        filtered_string += ' '.join([token for token in stripped_string.split(' ') if token and not (
            (token[0] in digits) or any(
                special_character in token for special_character in special_characters
            )
        )])

    return filtered_string


# The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "Usage: python manage.py rebuild_index <language> <version> --content_id=<e.g. documentation>"

    def get_docs_count(self):
        return len(self.documents) + len(self.api_documents)

    def add_arguments(self, parser):
        parser.add_argument('language', nargs='+')
        parser.add_argument('version', nargs='+')
        parser.add_argument(
            '--content_id', action='store', default=None, dest='content_id')


    def build_api_document(self, source_dir, lang):
        existing_docs_count = self.get_docs_count() + 1

        for subdir, dirs, all_files in os.walk(source_dir):
            for file in all_files:
                subpath = os.path.join(subdir, file)
                (name, extension) = os.path.splitext(file)

                # We explicitly only want to look at HTML files which are not indexes.
                if extension == '.html' and 'index_' not in file:
                    with open(os.path.join(settings.BASE_DIR, subpath)) as html_file:
                        soup = BeautifulSoup(html_file, 'lxml')

                        for api_call in soup.find_all(re.compile('^h(1|2|3)')):
                            parent_section = get_section_for_api_title(api_call)

                            title = next(api_call.stripped_strings)
                            content = parent_section.strings if parent_section else ''

                            if lang == 'zh':
                                content = jieba_zh_content(content) if content else content
                            elif content:
                                content = '. '.join(content)

                            try:
                                self.api_documents.append({
                                    'id': existing_docs_count,
                                    'path': '/' + subpath + (api_call.a['href'] if (api_call.a and api_call.a.has_attr('href')) else ''),
                                    'title': str(title.encode('utf-8')),
                                    'prefix': os.path.splitext(os.path.basename(name))[0] if '.' in name else '',
                                    'content': content.encode('utf-8')
                                })
                                existing_docs_count += 1

                            except Exception as e:
                                print("Unable to parse the file at: %s" % subpath)


    def build_document(self, source_dir, lang, version):
        existing_docs_count = self.get_docs_count() + 1
        apis_processed = False

        for subdir, dirs, all_files in os.walk(source_dir):
            for file in all_files:
                subpath = os.path.join(subdir, file)
                (name, extension) = os.path.splitext(file)

                # HACK: After version 1.1, API docs are within "docs", unlike before.
                # If we find this repo to contain an "api" directory under
                # documentation/docs/<language>/<version>/, send it
                # to be processed as a API folder.
                subpath_pieces = subpath.split('/')
                if len(subpath_pieces) > 5 and subpath_pieces[1] == 'docs' and (
                    subpath_pieces[4] in ['api', 'api_cn'] and not apis_processed):

                    # This means that anything before 1.2 should be treated as English
                    # because there was no Chinese API before that.
                    self.build_api_document(subdir, lang if version >= '1.2' else 'en')
                    apis_processed = True

                if extension == '.html':
                    document = {
                        'id': existing_docs_count,
                        'path': '/' + subpath
                    }

                    if document['path'] in self.unique_paths:
                        continue

                    # And extract their document content so that we can TFIDF
                    # their contents.
                    with open(
                        os.path.join(settings.BASE_DIR, subpath)) as html_file:
                        soup = BeautifulSoup(html_file, 'lxml')

                        # Find the first header 1 or h2.
                        title = soup.find('h1')
                        if not title:
                            title = soup.find('h2')

                        if title:
                            raw_title = next(title.stripped_strings)

                            if lang == 'zh':
                                document['title'] = jieba_zh_title(raw_title)
                                document['displayTitle'] = raw_title

                            else:
                                document['title'] = raw_title

                        else:
                            # No point trying to store a non-titled file
                            #     because it is probably a nav or index of sorts.
                            continue

                        # Segment the Chinese sentence through jieba library
                        # Temporarily jieba-ing even content.
                        # if lang == 'zh':
                        document['content'] = jieba_zh_content(
                            filter_insignificant_tokens(soup.stripped_strings)
                        )
                        # else:
                        #     document['content'] = ', '.join(soup.stripped_strings)

                    self.documents.append(document)
                    existing_docs_count += 1

                    self.unique_paths.append(document['path'])

                    print 'Indexing "%s"...' % document['title'].encode('utf-8')


    def handle(self, *args, **options):
        self.documents = []
        self.api_documents = []
        self.unique_paths = []

        contents_to_build = []
        if options['content_id']:
            contents_to_build.append(options['content_id'])
        else:
            for maybe_dir in os.listdir(settings.WORKSPACE_DIR):
                if os.path.isdir(
                    os.path.join(settings.WORKSPACE_DIR, maybe_dir)):
                    contents_to_build.append(maybe_dir)

        # First we need to go through all the generated HTML documents.
        version = sanitize_version(options['version'][0])

        for content_to_build in contents_to_build:
            source_dir = os.path.join(
                settings.WORKSPACE_DIR, content_to_build,
                options['language'][0], version
            )

            if content_to_build == 'api' and version not in ['0.10.0', '0.11.0']:
                self.build_api_document(source_dir, 'en')

            else:
                self.build_document(source_dir, options['language'][0], version)


        # And create an index JS file that we can import.
        output_index_dir = os.path.join(
            settings.INDEXES_DIR, 'indexes',
            options['language'][0], version
        )

        if not os.path.exists(output_index_dir):
            os.makedirs(output_index_dir)

        output_index_js = os.path.join(output_index_dir, 'index.js')
        output_toc_js = os.path.join(output_index_dir, 'toc.js')

        tmp_documents_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_documents_file.write(json.dumps(self.documents + self.api_documents))
        tmp_documents_file.close()

        with open(output_index_js, 'w') as index_file:
            index_file.write('module.exports = ' + check_output(['node',
                os.path.join(settings.PROJECT_ROOT, 'management/commands/build-index.js'), tmp_documents_file.name]))

        with open(output_toc_js, 'w') as toc_file:
            content_less_toc = {}

            for doc in self.documents + self.api_documents:
                if doc['path'] not in content_less_toc:
                    serialized_doc = {
                        'id': doc['id'],
                        'path': doc['path'],
                        'title': doc['displayTitle'] if 'displayTitle' in doc else doc['title']
                    }

                    if 'prefix' in doc:
                        serialized_doc['prefix'] = doc['prefix']

                    content_less_toc[doc['id']] = serialized_doc

            toc_file.write('module.exports = ' + json.dumps(content_less_toc))

        os.remove(tmp_documents_file.name)

        # Gzip the index generated.
        # NOTE: Will make NGINX do this on the fly.
        # check_output(['gzip', output_index_js])
        # check_output(['gzip', output_toc_js])
