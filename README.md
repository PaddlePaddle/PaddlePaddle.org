# PaddlePaddle.org's Open-Source Content + API Documentation Generator

This repo contains all the tools to generate the English and Chinese version of the official website for [PaddlePaddle](https://github.com/PaddlePaddle/Paddle): an easy-to-use, efficient, and scalable distributed deep learning platform. Tied with [Django](https://www.djangoproject.com/), these tools augment [Sphinx](http://www.sphinx-doc.org/en/master/)'s documentation generation capabilities.

The tutorials here guide you to setup the website locally, so you can see exactly how your contributions will appear on [paddlepaddle.org](http://paddlepaddle.org).


## Installation

1. Since this repo does not hold the content rendered on website, download / clone ONLY the relevant repos with content and code that you want to render (if you don't already have them):
   - [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) (contains all articles AND codebase to render the API documentation)
   - [Book](https://github.com/PaddlePaddle/book) (contains chapter pages)
   - [Models](https://github.com/PaddlePaddle/models) (contains the code to build models for different applications, including a few articles)
   - [Mobile](https://github.com/PaddlePaddle/mobile) (contains articles for building for mobile)

   You can place these anywhere on the computer; at a later step we will tell PaddlePaddle.org where they are.


2. Pull PaddlePaddle.org and install its dependencies in a new directory.

   ```git clone git@github.com:PaddlePaddle/PaddlePaddle.org.git
   cd portal; pip install -r requirements.txt
   ```

3. Run PaddlePaddle.org



## Writing new content





```

#### 2) Open up your browser and navigate to [http://localhost:8000](http://localhost:8000).

### Documentation Generation and Viewer Tool (For Documentation creators)

#### 1) Clone Paddle repositories
NOTE: Skip this step if you already have a local copy of these repos.
```
mkdir paddlepaddle
cd paddlepaddle
git clone git@github.com:PaddlePaddle/Paddle.git
git clone git@github.com:PaddlePaddle/book.git
git clone git@github.com:PaddlePaddle/models.git
```

Now your directories should look like:

```
- paddlepaddle
    - Paddle
    - book
    - models
    - mobile
```

#### 2) Run PaddlePaddle.org Docker Image within the *paddlepaddle* directory.
**Note:** PaddlePaddle.org will read the content repos specified in the -v (volume) flag of the docker run command

```
docker run -it -p 8000:8000 -v `pwd`:/var/content paddlepaddle/paddlepaddle.org:latest
```

#### 3) Open up your browser and navigate to [http://localhost:8000](http://localhost:8000).

### Don't want to use Docker?
You can also run through Django framework directly to activate the tool server. Use the following commands to run it.

#### 1) Clone Paddle repositories
```
mkdir paddlepaddle
cd paddlepaddle
git clone git@github.com:PaddlePaddle/Paddle.git
git clone git@github.com:PaddlePaddle/book.git
git clone git@github.com:PaddlePaddle/models.git
git clone git@github.com:PaddlePaddle/PaddlePaddle.org.git
```

#### 2) Run PaddlePaddle.org through Django within the *paddlepaddle* directory.
```
export CONTENT_DIR=<path_to_paddlepaddle_working_directory>
export ENV=''
cd PaddlePaddle.org/portal/
pip install -r requirements.txt
python manage.py runserver
```
#### 3) Open up your browser and navigate to [http://localhost:8000](http://localhost:8000).

## Additional Resources
- To develop on PaddlePaddle.org, please refer to [Development Guide](DEVELOPING.md)
- Information about how content repositories are structured and consumed: [Content repositories](CONTENT_REPO.md)


## Contributing to improve the tools

We appreciate contribution to various aspects of the platform and supporting content, apart from better presenting these materials. You may fork or clone this repository, or begin asking questions and providing feedback and leave bug reports on Github Issues.


## Copyright and License

PaddlePaddle.org is provided under the [Apache-2.0 license](https://github.com/PaddlePaddle/Paddle/blob/develop/LICENSE).
