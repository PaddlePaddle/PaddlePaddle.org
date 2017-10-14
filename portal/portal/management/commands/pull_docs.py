import os
import shutil
import tempfile

from exceptions import OSError
from django.core.management import BaseCommand
from git import Repo
from git.exc import GitCommandError


# The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "Usage: python manage.py pull_docs <version> <dest_dir>"

    def add_arguments(self, parser):
        parser.add_argument('version', nargs='+')
        parser.add_argument('dest_dir', nargs='+', )

    # A command must define handle()
    def handle(self, *args, **options):
        book_repo_path = 'git@github.com:PaddlePaddle/book.git'
        models_repo_path = 'git@github.com:PaddlePaddle/models.git'
        blog_repo_path = 'git@github.com:PaddlePaddle/blog.git'
        documentations_repo_path = 'git@github.com:PaddlePaddle/Paddle.git'

        temp_dir = '%s/tmp_repo' % tempfile.gettempdir()
        book_dir = '%s/book' % temp_dir
        models_dir = '%s/models' % temp_dir
        documentations_dir = '%s/documentations' % temp_dir

        print 'Temp working dir: %s' % temp_dir
        try:
            # Set dest_dict
            dest_dir_list = options['dest_dir']
            dest_dir = dest_dir_list[0] if dest_dir_list else None

            if not dest_dir:
                raise "No dest_dir specified"
            else:
                print "Destination: %s" % dest_dir

            # Clone Repos
            print "Clone Book repo"
            Repo.clone_from(book_repo_path, book_dir)

            print "Clone Models repo"
            Repo.clone_from(models_repo_path, models_dir)

            print "Clone Documentations repo"
            Repo.clone_from(documentations_repo_path, documentations_dir)

            # Blog is not versioned. Pull the master branch to update contents.
            blog_dir = '%s/blog' % dest_dir
            if os.path.exists(blog_dir):
                print "Update existing Blog repo"
                blog_repo = Repo(blog_dir)
                blog_repo.git.checkout('master')
                blog_repo.git.pull()
            else:
                print "Clone Blog repo"
                Repo.clone_from(blog_repo_path, blog_dir)

            book_repo = Repo(book_dir)
            models_repo = Repo(models_dir)
            documentations_repo = Repo(documentations_dir)

            if 'version' in options:
                for version in options['version']:
                    print 'Prepare version: %s' % version
                    version_dir = '%s/%s' % (dest_dir, version)

                    # Create the dest folder
                    if not os.path.exists(version_dir):
                        print "Create dir at: %s" % version_dir
                        os.makedirs(version_dir)

                    print "Start copying version: %s into dest dir" % version

                    book_doc_dest = '%s/book' % version_dir
                    self._copy_content(book_repo, version, book_dir, book_doc_dest, 'Book')

                    models_doc_dest = '%s/models' % version_dir
                    self._copy_content(models_repo, version, models_dir, models_doc_dest, 'Models')

                    documentations_doc_dest = '%s/documentation' % version_dir
                    self._copy_content(documentations_repo, version, documentations_dir, documentations_doc_dest, 'Documentations')

        except Exception as e:
            print 'Unexpected error cloning repos: %s' % e
        finally:
            # Clean up the temp folder
            if os.path.exists(temp_dir):
                print 'Remove temp content dir'
                shutil.rmtree(temp_dir)
            print "BYE"

    def _copy_content(self, repo, version, doc_src, doc_dest, name):
        try:
            repo.git.checkout(version)
            print "Copy %s data to %s" % (name, doc_dest)
            shutil.copytree(doc_src, doc_dest, symlinks=True)
        except GitCommandError as e:
            print "Skip %s content. Unable to checkout %s branch! Exception: %s" % (name, version, e)
        except OSError as e:
            print "Skip %s content. Content exists already. Exception: %s" % (name, e)
        except Exception as e:
            print "Skip %s Content. Exception: %s" % (name, e)
