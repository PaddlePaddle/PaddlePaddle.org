# -*- coding: utf-8 -*-
import os
import json
from bs4 import BeautifulSoup
from django.conf import settings


def sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    pass


def book_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    pass


def models_sitemap(original_documentation_dir, generated_documentation_dir, version, output_dir_name):
    github_path = 'https://github.com/PaddlePaddle/models/tree/develop'

    # Create models sitemap template
    sections = []
    sitemap = {"title": {"zh": "概述"}, 'sections': sections}

    # Read the stripped html file
    # TODO [Jeff Wang]: Confirm the root_html_path is correct
    root_html_path = os.path.join(generated_documentation_dir, 'README.html')
    with open(root_html_path) as original_html_file:
        soup = BeautifulSoup(original_html_file, 'lxml')

        anchor_tags = soup.select('li a[href]')
        # Extract the links and the article titles
        for tag in anchor_tags:
            title = {'zh': tag.text}
            # The absolute URLs link to the github site. Transform them into relative URL for local HTML files.
            link_zh = tag['href'].replace(github_path, 'models/') + '/README.html'
            link = {'zh': link_zh}

            section = {'title': title, 'link': link}
            sections.append(section)

    # TODO [Jeff Wang]: Confirm the models sitemap path is correct
    versioned_dest_dir = _get_destination_documentation_dir(version, output_dir_name)
    if not os.path.isdir(versioned_dest_dir):
        os.makedirs(versioned_dest_dir)
    sitemap_path = os.path.join(versioned_dest_dir, 'site.json')
    # Update the models.json
    with open(sitemap_path, 'w') as outfile:
        json.dump(sitemap, outfile)


def _get_destination_documentation_dir(version, output_dir_name):
    return '%s/docs/%s/%s' % (settings.EXTERNAL_TEMPLATE_DIR, version, output_dir_name)
