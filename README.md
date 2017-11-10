# PaddlePaddle.org

**PaddlePaddle.org** is the repository for the website of the [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) open source project: an easy-to-use, efficient, and scalable distributed deep learning platform. The goal is to provide a unified web access to all code and documentation related to the PaddlePaddle project. The website is designed to yield uniform user experience and provide access to the latest information about PaddlePaddle.

## Contributing to PaddlePaddle.org

We appreciate contribution to various aspects of the platform and supporting content, apart from better presenting these materials.

You may fork or clone this repository, or begin asking questions and providing feedback and leave bug reports on Github Issues.

## PaddlePaddle.org Document Generation and Viewer Tool

**Prerequisites**:  Docker is required in order to run PaddlePaddle.org doucmentation viewer.
[Install Docker Here](https://docs.docker.com/engine/installation/).

PaddlePaddle.org not only powers [http://paddlepaddle.org](http://paddlepaddle.org), it can be used as a tool for documentation creators to generate and view their documentation on their local machine.  To run PaddlePaddle.org as a Document tool, please take a look of the  tutorial video or follow the instructions below:

### Documentation Viewer Only Tool

##### Video Tutorial
https://github.com/bobateadev/images/raw/master/viewer_tool_demo_cn.mp4 (Chinese version)
https://github.com/bobateadev/images/raw/master/viewer_tool_demo.mp4 (English version)
#### 1) Run PaddlePaddle.org Docker Image. 
```
docker run -d -p 8000:8000 paddlepaddle/paddlepaddle.org:latest
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
docker run -d -p 8000:8000 -v `pwd`:/var/content paddlepaddle/paddlepaddle.org:latest
```

#### 3) Open up your browser and navigate to [http://localhost:8000](http://localhost:8000).

## Additional Resources
- To develop on PaddlePaddle.org, please refer to [Development Guide](DEVELOPING.md)
- Information about how content repositories are structured and consumed: [Content repositories](CONTENT_REPO.md)

## Copyright and License

PaddlePaddle.org is provided under the [Apache-2.0 license](https://github.com/PaddlePaddle/Paddle/blob/develop/LICENSE).

