# PaddlePaddle.org's content + API documentation generator

This repo contains all the tools to generate the English and Chinese version of the official website for [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) (an easy-to-use, efficient, and scalable distributed deep learning platform). Tied with [Django](https://www.djangoproject.com/), these tools augment [Sphinx](http://www.sphinx-doc.org/en/master/)'s documentation generation capabilities.

The tutorials here guide you to setup the website locally, so you can see exactly how your contributions will appear on [paddlepaddle.org](http://paddlepaddle.org).


## Installation

1. **Since this repo does not hold the content rendered on website, download / clone ONLY the relevant repos with content and code that you want to update and test (if you don't already have them):**
   - [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) (contains all articles AND codebase to render the API documentation)
   - [Book](https://github.com/PaddlePaddle/book) (contains chapter pages)
   - [Models](https://github.com/PaddlePaddle/models) (contains the code to build models for different applications, including a few articles)
   - [Mobile](https://github.com/PaddlePaddle/mobile) (contains articles for building for mobile)

   You can place these anywhere on the computer; at a later step we will tell PaddlePaddle.org where they are.


2. **Pull PaddlePaddle.org into a new directory and install its dependencies.**

    ```
    git clone git@github.com:PaddlePaddle/PaddlePaddle.org.git
    cd portal
    pip install -r requirements.txt
    ```

    *Optional: If you plan on translating website content between English and Chinese for improving PaddlePaddle.org, install [GNU gettext](https://www.gnu.org/software/gettext/) too.*


3. **Run PaddlePaddle.org locally.**

    Pass the list of directories you wish to load and build content from (options include `--paddle`, `--book`, `--models`, and `--mobile`)
    ```
    ./runserver --paddle <path_to_paddle_doc_version_dir> --book <path_to_book_dir>
    ```

    *NOTE: In case of the --paddle directory, point to the specific API version directory (e.g. `fluid` or `v2`).*

    Open up your browser and navigate to [http://localhost:8000](http://localhost:8000).
    **NOTE**: *Links may take a few seconds to load the first time around since they are probably being built.*


## Writing new content

All repositories support content contribution formatted as [Markdown](https://guides.github.com/features/mastering-markdown/) (the GitHub flavor). The Paddle repo, where majority of the documentation lies, also support the [reStructured Text](http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) format.

After you have gone through the installation steps above, here are the steps you need to take:

- Before you start writing, we recommend reviewing these [guidelines on contributing content]().
- Create a new `.md` (or `.rst`, only in the case of Paddle) file OR edit an existing article's file within the appropriate directory of the repo you are contributing to.
- To view the changes in your browser, click **Refresh Content** on the top-righthand side corner.
- To add it to a menu or change its position on the menu, click on the **Edit menu** button at the top of the left-handside menu on the page, to open the menu editor.


## Writing or modifying the Python API

After you have built your new `pybind` targets, and have tested your new Python API, you can continue with testing how your documentation strings and comments show up:

- We recommend reviewing these [guidelines on contributing API documentation]().
- Make sure that the built Python directory (containing `paddle`) is available in the `PYTHONPATH` of where you are running `./runserver` from.
- On the specific "API" page you wish to update, click **Refresh Content** on the top-righthand side corner.
- To add it to a menu or change its position on the menu, click on the **Edit menu** button at the top of the left-handside menu on the page, to open the menu editor.



<!---
## Writing or modifying APIs

There are two kinds of API updates you can make: the Python API for users, and the list of available operators. Before you are ready to test how your documentation strings and comments show, we recommend reviewing these [guidelines on contributing API documentation]().


### Python API updates

- On the specific "API" page you wish to update, click **Regenerate** on the top-righthand side corner.
- To add it to a menu or change its position on the menu, click on the **Edit menu** button at the top of the left-handside menu on the page, to open the menu editor.


### Operators updates

If you have added or removed operators, or made changes to their "RDOC", after you build your new `pybind` targets, also build the `operators`
--->


## Contributing to improve the tools

We appreciate contribution to various aspects of the platform and supporting content, apart from better presenting these materials. You may fork or clone this repository, or begin asking questions and providing feedback and leave bug reports on Github Issues. Please refer to [Development Guide](DEVELOPING.md) on how to get started.


## Copyright and License

PaddlePaddle.org is provided under the [Apache-2.0 license](https://github.com/PaddlePaddle/Paddle/blob/develop/LICENSE).
