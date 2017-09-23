from django.conf import settings


def get_tutorial_links():
    """
    1) call _get_root_csf()
    2) using root CSF to generate link map for Tutorial page

    Tutorial == book
    """
    pass


def _get_root_csf():
    """
    1) determine if root content schematic file (CSF) exists in content directory
    2) if root CSF does not exist or is out of date, generate CSF for each content directory (doc, blog, book, models)
    3) once each CSF is built, merge them to form root CSF and save them in content directory
    4) if no errors, return root csf, otherwise throw exception
    """
    pass


class ContentSchematicFile():
    def __init__(self):
        self.file_path = settings.EXTERNAL_TEMPLATE_DIR + 'root_csf.yaml'
        self.csf_data = None  # dict

    def is_valid(self):
        """
        check if csf exists and not expired
        """
        pass

    @staticmethod
    def get_site_csf():
        """
        returns a csf if it exists and valid, otherwise generate the root csf and returns it when complete
        throws exceptions once there are errors

        return ContentSchematicFile.generate_csf( SiteMapCSFAdapter() )
        """
        pass

    @staticmethod
    def generate_csf(csf_adapter=None):
        """
        generate csf
        """
        pass


class CSFAdapter:
    def __init__(self):
        pass

    def parse(self):
        raise NotImplementedError("Should have implemented this")


class DirectoryCSFAdapter(CSFAdapter):
    def __init__(self, dir):
        self.dir = dir

    def parse(self):
        """
        go through files in dir and generate CSF.json for each content directory
        """
        pass


class SiteMapCSFAdapter(CSFAdapter):
    def parse(self):
        """
        combine content dir CSFs into a root CSF

        ex:
        blogCFS = ContentSchematicFile.generate_csf( DirectoryCSFAdapter('/var/content/blog') )
        documentCFS = ContentSchematicFile.generate_csf( DirectoryCSFAdapter('/var/content/document') )

        // TODO: merge blogCFS && documentCFS to create root CSF and return
        """
        pass