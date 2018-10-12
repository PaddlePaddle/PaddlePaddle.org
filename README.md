# PaddlePaddle.org's content + API documentation generator

This repo contains all the tools to generate the English and Chinese version of the official website for [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) (an easy-to-use, efficient, and scalable distributed deep learning platform). Tied with [Django](https://www.djangoproject.com/), these tools augment [Sphinx](http://www.sphinx-doc.org/en/master/)'s documentation generation capabilities.

The tutorials here guide you to setup the website locally, so you can see exactly how your contributions will appear on [paddlepaddle.org](http://paddlepaddle.org).


## Installation

If you are working on improving code documentation (i.e. APIs) and are within a Docker container with PaddlePaddle, perform these steps within the container. You need to do this because the documentation generator for APIs has a dependency on PaddlePaddle.

On the other hand, if you are only improving the text/media content (since you don't need an installed or built PaddlePaddle) OR are building PaddlePaddle on your (host) machine, continue on your host machine.


1. **Download / clone the documentation repo (the PaddlePaddle.org repo does not contain the content):**

    ```bash
    git clone --recurse-submodules https://github.com/PaddlePaddle/FluidDoc
    ```

   You can place this anywhere on the computer; at a later step we will tell PaddlePaddle.org where it is.


2. **Pull PaddlePaddle.org into a new directory and install its dependencies.**

    But before that, make sure you have Python dependencies installed on your OS. For example, on an Ubuntu, run:
    ```bash
    sudo apt-get update && apt-get install -y python-dev build-essential
    ```

    Then,
    ```bash
    git clone https://github.com/PaddlePaddle/PaddlePaddle.org.git
    cd PaddlePaddle.org/portal

    # To install in a virtual environment.
    # virtualenv venv; source venv/bin/activate

    pip install -r requirements.txt
    ```

    *Optional: If you plan on translating website content between English and Chinese for improving PaddlePaddle.org, install [GNU gettext](https://www.gnu.org/software/gettext/) too.*


3. **Run PaddlePaddle.org (locally or through the Docker container).**

    Pass the cloned FluidDoc directory:

    ```bash
    ./runserver --paddle <path_to_fluiddoc_dir> --book <path_to_book_dir>
    ```

    Open up your browser and navigate to [http://localhost:8000](http://localhost:8000).

    In the case you were working on the English documentation that depends on content within the `book`, `models`, or `mobile` repositories, you may also pass one or more of the following options:

    ```bash
    ./runserver --paddle <path_to_fluiddoc_dir> \
        --book <path_to_fluiddoc_dir>/external/book \
        --models <path_to_fluiddoc_dir>/external/models \
        --mobile <path_to_fluiddoc_dir>/external/mobile
    ```

    **NOTE**: *Links may take a few seconds to load the first time around since they are probably being built.*

    **ANOTHER NOTE**: *If you are doing this step through a Docker environment, make sure to map the port 8000 to your host machine*


## Previewing new documentation or updating APIs

All content should be written in [Markdown](https://guides.github.com/features/mastering-markdown/) (the GitHub flavor) (even though there are some legacy pieces of content in `docs` using the `.rst` format).

After you have gone through the installation steps above, here are the steps you need to take:

- Before you start writing, we recommend reviewing these [guidelines on contributing content](https://github.com/PaddlePaddle/PaddlePaddle.org/wiki/Markdown-syntax-guideline).

---


### If you are writing new content:
- Create a new `.md` file OR edit an existing article's file within the appropriate directory of the repo you are contributing to.


### If you have updated the API comments and want to preview the updates:

Inside the Docker or host machine where Paddle is to be rebuilt, either:
-  Run the the script `paddle/scripts/paddle_build.sh` (from the main Paddle repository / codebase).

-  **OR** (if you want control / understanding over the process):
   - Create a new directory in the `Paddle` repo to build Paddle into. Let's call it `build`, for example.
   - Within this new directory, run the following `cmake` and `make` commands to build a new PaddlePaddle:

     ```bash
     cmake .. -DCMAKE_BUILD_TYPE=Release -DWITH_DOC=ON -DWITH_GPU=OFF -DWITH_MKL=OFF -DWITH_FLUID_ONLY=ON

     # You may replace `nproc` with the number of processor cores your system can offer for the build.
     make -j `nproc` gen_proto_py framework_py_proto copy_paddle_pybind paddle_python
     ```

   - Export the environment variable `PYTHONPATH` to include the this new `build` directory (or whatever you named it)


Note that if you are using Docker, `paddle_docker_build.sh` rebuilds a new Docker container. This destroys the PaddlePaddle.org installation on that Docker instance, so it is not the suggested way to rebuild your code if you wish to preview documentation.

---

- To view the changes in your browser, click **Refresh Content** on the top-righthand side corner.


## Submitting your documentation changes

If you have made changes to the code, you need to follow the contribution guidelines on the `paddle` repo.

On the other hand, if you have pure documentation updates:

- If you changed contents in the `doc` folder, you only need to submit a PR to the `FluidDoc` repo.

- On the other hand, if you changed anything in the external folder:
  - Submit a PR on the repo whose content you have changed. The `FluidDoc` repo is simply a wrapper that houses links (or in git terminology, "sub-modules") to other repos.
  - After it is approved, change the git sub-module pointer to the new commit from the source repo. For example, say you updated contents of the `book` repo.
    - Go into the `book` dir.
    - Checkout the commit on the `book` repo you wish to update to.
    - And now commit the new changes to the `FluidDoc` repo.

  - Submit a PR on the `FluidDoc` repo with this change.


## Contributing to improve the tools

We appreciate contribution to various aspects of the platform and supporting content, apart from better presenting these materials. You may fork or clone this repository, or begin asking questions and providing feedback and leave bug reports on Github Issues. Please refer to [Development Guide](DEVELOPING.md) on how to get started.


## Copyright and License

PaddlePaddle.org is provided under the [Apache-2.0 license](https://github.com/PaddlePaddle/Paddle/blob/develop/LICENSE).
