# PaddlePaddle.org's content + API documentation generator

This repo contains all the tools to generate the English and Chinese version of the official website for [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) (an easy-to-use, efficient, and scalable distributed deep learning platform). Tied with [Django](https://www.djangoproject.com/), these tools augment [Sphinx](http://www.sphinx-doc.org/en/master/)'s documentation generation capabilities.

The tutorials here guide you to setup the website locally, so you can see exactly how your contributions will appear on [paddlepaddle.org](http://paddlepaddle.org).


## Installation

1. Since this repo does not hold the content rendered on website, download / clone ONLY the relevant repos with content and code that you want to update and test (if you don't already have them):
   - [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) (contains all articles AND codebase to render the API documentation)
   - [Book](https://github.com/PaddlePaddle/book) (contains chapter pages)
   - [Models](https://github.com/PaddlePaddle/models) (contains the code to build models for different applications, including a few articles)
   - [Mobile](https://github.com/PaddlePaddle/mobile) (contains articles for building for mobile)

   You can place these anywhere on the computer; at a later step we will tell PaddlePaddle.org where they are.


2. Pull PaddlePaddle.org into a new directory and install its dependencies.
    ```
    git clone git@github.com:PaddlePaddle/PaddlePaddle.org.git
    cd portal; pip install -r requirements.txt
    ```

3. Run PaddlePaddle.org locally.
    Pass the list of directories you wish to load and build content from (options include `-paddle`, `-book`, `-models`, and `-mobile`)
    ```
    ./runserver -paddle <path to paddle dir> -book <path to book dir>
    ```

    Open up your browser and navigate to [http://localhost:8000](http://localhost:8000).


## Writing new content





```

## Additional Resources
- To develop on PaddlePaddle.org, please refer to [Development Guide](DEVELOPING.md)
- Information about how content repositories are structured and consumed: [Content repositories](CONTENT_REPO.md)


## Contributing to improve the tools

We appreciate contribution to various aspects of the platform and supporting content, apart from better presenting these materials. You may fork or clone this repository, or begin asking questions and providing feedback and leave bug reports on Github Issues.


## Copyright and License

PaddlePaddle.org is provided under the [Apache-2.0 license](https://github.com/PaddlePaddle/Paddle/blob/develop/LICENSE).
