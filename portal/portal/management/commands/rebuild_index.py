import os
import re
import json
import math

import nltk
from textblob import TextBlob as tb
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management import BaseCommand


# Adopted from https://stevenloria.com/tf-idf/.
def tf(word, blob):
    return blob.words.count(word) / len(blob.words)

def n_containing(word, bloblist):
    return sum(1 for blob in bloblist if word in blob.words)

def idf(word, bloblist):
    return math.log(len(bloblist) / (1 + n_containing(word, bloblist)))

def tfidf(word, blob, bloblist):
    return tf(word, blob) * idf(word, bloblist)


# The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # TODO(Varun): Do a non-hardcoded approach here.
    API_DOCUMENTS = [
        'evaluator', 'executor', 'initializer', 'io', 'layers',
        'nets', 'optimizer', 'regularizer'
    ]

    # Show this when the user types help
    help = "Usage: python manage.py rebuild_index <language> <version> --content_id=<e.g. documentation>"

    def add_arguments(self, parser):
        parser.add_argument('language', nargs='+')
        parser.add_argument('version', nargs='+')
        parser.add_argument(
            '--content_id', action='store', default=None, dest='content_id')


    def build_api_document(self, source_file):
        with open(os.path.join(settings.BASE_DIR, source_file)) as html_file:
            soup = BeautifulSoup(html_file, 'lxml')

            api_calls = soup.find_all(re.compile('^h'))

            for api_call in api_calls:
                self.api_documents.append({
                    'path': '/' + source_file + api_call.a['href'],
                    'title': str(next(api_call.stripped_strings)),
                    'prefix': os.path.splitext(os.path.basename(source_file))[0]
                })


    def build_document(self, source_dir):
        for subdir, dirs, all_files in os.walk(source_dir):
            for file in all_files:
                subpath = os.path.join(subdir, file)
                (name, extension) = os.path.splitext(file)

                if extension == '.html' and name not in self.API_DOCUMENTS:
                    document = {
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
                            document['title'] = next(title.stripped_strings)
                        else:
                            # No point trying to store a non-titled file
                            #     because it is probably a nav or index of sorts.
                            continue

                        document['content'] = ', '.join(soup.stripped_strings)

                    self.documents.append(document)
                    self.unique_paths.append(document['path'])

                    print 'Found "%s"...' % document['title']


    def handle(self, *args, **options):
        self.documents = []
        self.api_documents = []
        self.unique_paths = []

        nltk.download('punkt')

        contents_to_build = []
        if options['content_id']:
            contents_to_build.append(options['content_id'])
        else:
            for maybe_dir in os.listdir(settings.WORKSPACE_DIR):
                if os.path.isdir(
                    os.path.join(settings.WORKSPACE_DIR, maybe_dir)):
                    contents_to_build.append(maybe_dir)

        # First we need to go through all the generated HTML documents.
        for content_to_build in contents_to_build:
            source_dir = os.path.join(
                settings.WORKSPACE_DIR, content_to_build,
                options['language'][0], options['version'][0]
            )

            if content_to_build == 'api' and options['version'][0] not in ['0.10.0', '0.11.0']:
                # Get the name of all the files in the API dir.
                for api_document in self.API_DOCUMENTS:
                    self.build_api_document(os.path.join(
                        source_dir, api_document + '.html'))
            else:
                self.build_document(source_dir)

        # Using this content, we build tfidf for all the content.
        document_contents = [tb(
            doc['content']) for doc in self.documents if 'content' in doc]
        for document_index, document_content in enumerate(document_contents):
            if not document_content:
                continue
            print 'Indexing', self.documents[document_index]['title']

            scores = { word: tfidf(
                word, document_content, document_contents) for (
                word) in document_content.words }
            sorted_words = sorted(
                scores.items(), key=lambda x: x[1], reverse=True)
            self.documents[document_index]['content'] = [word[0].encode(
                'utf-8') for word in sorted_words[:20]]

        # And create an index JS file that we can import.
        output_index_js = os.path.join(
            settings.STATICFILES_DIRS[0],
            'indexes', options['version'][0], 'index.js'
        )

        if not os.path.exists(os.path.dirname(output_index_js)):
            # Generate the directory.
            os.makedirs(os.path.dirname(output_index_js))

        with open(output_index_js, 'w') as index_file:
            index_file.write('var index = ' + json.dumps(
                self.documents + self.api_documents))
