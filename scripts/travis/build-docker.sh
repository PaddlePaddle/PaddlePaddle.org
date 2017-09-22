#!/bin/bash
set -e

# Builds the docker image for PaddlePaddle.org

if [[ "$TRAVIS_BRANCH" =~ ^v[[:digit:]]+\.[[:digit:]]+(\.[[:digit:]]+)?(-\S*)?$ ]]
then
    # Production Deploy, only on tags matching format (ie: v1.3)
    echo "Building for PROD: $TRAVIS_BRANCH"
    export DOCKER_IMAGE_TAG="latest"
elif [[ "$TRAVIS_BRANCH" =~ ^release.*$ ]]
then
    # Staging Deploy
    echo "Building for STAGING"
    export DOCKER_IMAGE_TAG="staging"
elif [ "$TRAVIS_BRANCH" == "develop" ]
then
    # Development Deploy
    echo "Building for DEVELOP"
    export DOCKER_IMAGE_TAG="develop"
else
    # All other branches should be ignored
    echo "Cannot build image, invalid branch: $TRAVIS_BRANCH"
    exit 1
fi

docker --version  # document the version travis is using
docker build -t paddlepaddle.org:"$DOCKER_IMAGE_TAG" .
