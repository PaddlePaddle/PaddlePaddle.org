import os
import json
from bs4 import BeautifulSoup


def sphinx_sitemap(original_documentation_dir, generated_documentation_dir, version, destination_documentation_dir):
    pass


def book_sitemap(original_documentation_dir, generated_documentation_dir, version, destination_documentation_dir):
    pass


def models_sitemap(original_documentation_dir, generated_documentation_dir, version, destination_documentation_dir):
    github_path = 'https://github.com/PaddlePaddle/models/tree/'

    # Create models sitemap template
    models_sitemap = {"title": {"zh": "models"}}
    models_sitemap['sections'] = []

    # Read the stripped html file
    # TODO [Jeff Wang]: Confirm the root_html_path is correct
    root_html_path = os.path.join(generated_documentation_dir, 'README.html')
    with open(root_html_path) as original_html_file:
        soup = BeautifulSoup(original_html_file, 'lxml')

        anchor_tags = soup.select('li a[href]')
        # Extract the links and the article titles
        for tag in anchor_tags:
            title = {'zh': tag.text}
            link_zh = tag['href'].replace(github_path, '') + '/README.html'
            link = {'zh': link_zh}

            section = {'title': title, 'link': link}
            models_sitemap['sections'].append(section)

    # TODO [Jeff Wang]: Confirm the models sitemap path is correct
    # Update the models.json
    sitemap_path = os.path.join(destination_documentation_dir, 'models.json')
    with open(sitemap_path, 'w') as outfile:
        json.dump(models_sitemap, outfile)

