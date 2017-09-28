import json
import os
import re
from django.conf import settings
from stat import *


def get_tutorial_links():
    obj = SiteMapCSFAdapter()
    obj.parse()


class ContentSchematicFile():
    @staticmethod
    def iterate_folder(top, paths, is_chinese=False):
        for f in os.listdir(top):
            pathname = os.path.join(top, f)
            mode = os.stat(pathname)[ST_MODE]
            if S_ISDIR(mode):
                ContentSchematicFile.iterate_folder(pathname, paths, is_chinese=is_chinese)
            elif S_ISREG(mode):
                pieces = pathname.split('.')
                if pieces[-1] == 'html':
                    if is_chinese:
                        matchObj = re.match(r'^.*(\d{2})\.(.*)/.*cn\.html$', pathname)
                    else:
                        matchObj = re.match(r'^.*(\d{2})\.(.*)/.*index\.html$', pathname)

                    if matchObj:
                        title = ' '.join(matchObj.group(2).split('_'))
                        link = pathname[len(settings.EXTERNAL_TEMPLATE_DIR):]
                        paths.append({
                            "title": title,
                            "link": link
                        })
            else:
                continue

    @staticmethod
    def generate_book_csf(site_dir, id="", title=""):
        """
        generate csf
        """
        if os.path.exists(site_dir + '/site.json') and os.path.exists(site_dir + '/site_cn.json'):
            return

        sections = []
        ContentSchematicFile.iterate_folder(site_dir, sections, is_chinese=False)

        cur_csf = {id: {"title": title, "sections": sections}}

        with open(site_dir + '/site.json', 'w') as fp:
            fp.write(json.dumps(cur_csf))

        sections = []
        ContentSchematicFile.iterate_folder(site_dir, sections, is_chinese=True)

        cur_csf = {id: {"title": title, "sections": sections}}

        with open(site_dir + '/site_cn.json', 'w') as fp:
            fp.write(json.dumps(cur_csf))

        return cur_csf


class SiteMapCSFAdapter():
    def parse(self):
        """
        combine content dir CSFs into a root CSF

        ex:
        blogCFS = ContentSchematicFile.generate_csf( DirectoryCSFAdapter('/var/content/blog') )
        documentCFS = ContentSchematicFile.generate_csf( DirectoryCSFAdapter('/var/content/document') )

        // TODO: merge blogCFS && documentCFS to create root CSF and return
        """
        bookCFS = ContentSchematicFile.generate_book_csf(
            settings.EXTERNAL_TEMPLATE_DIR + '/book',
            id="tutorial",
            title="Deep Learning 101"
        )
