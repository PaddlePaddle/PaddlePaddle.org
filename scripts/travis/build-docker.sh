#!/bin/bash
set -e

# Builds the docker image for PaddlePaddle.org

if [ "$TRAVIS_BRANCH" == "master" ]
then
    # Production Deploy
    export DOCKER_IMAGE_TAG="latest"
elif [[ "$TRAVIS_BRANCH" =~ ^release.*$ ]]
then
    # Staging Deploy
    export DOCKER_IMAGE_TAG="staging"
elif [ "$TRAVIS_BRANCH" == "develop" ]
then
    # Development Deploy
    export DOCKER_IMAGE_TAG="develop"
else
    # All other branches should be ignored
    echo "Cannot build image, invalid branch: $TRAVIS_BRANCH"
    exit 1
fi

docker --version  # document the version travis is using
docker build -t paddlepaddle.org:"$DOCKER_IMAGE_TAG" .
