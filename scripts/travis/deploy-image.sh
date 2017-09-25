#!/bin/bash
set -e

if [[ "$TRAVIS_BRANCH" =~ ^v[[:digit:]]+\.[[:digit:]]+(\.[[:digit:]]+)?(-\S*)?$ ]]
then
    # Production Deploy
    echo "Deploying to PROD"
    export DOCKER_IMAGE_TAG="latest"
    export BUILD_TAG="$TRAVIS_BRANCH"
    export DOCKER_CONTAINER_NAME="paddlepaddle.org"
    export PORT=80
    export ENV=release
elif [[ "$TRAVIS_BRANCH" =~ ^release.*$ ]]
then
    # Staging Deploy
    echo "Deploying to STAGING"
    export DOCKER_IMAGE_TAG="staging"
    export DOCKER_CONTAINER_NAME="staging.paddlepaddle.org"
    export PORT=81
    export ENV=release
elif [ "$TRAVIS_BRANCH" == "develop" ]
then
    # Development Deploy
    echo "Deploying to DEVELOP"
    export DOCKER_IMAGE_TAG="develop"
    export DOCKER_CONTAINER_NAME="develop.paddlepaddle.org"
    export PORT=82
    export ENV=development
else
    # All other branches should be ignored
    echo "Cannot deploy image, invalid branch: $TRAVIS_BRANCH"
    exit 1
fi

eval $(aws ecr get-login --no-include-email --region ap-southeast-1) #needs AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY envvars


# Tag and push image
docker tag paddlepaddle.org:"$DOCKER_IMAGE_TAG" 330323714104.dkr.ecr.ap-southeast-1.amazonaws.com/paddlepaddle.org:"$DOCKER_IMAGE_TAG"
docker push 330323714104.dkr.ecr.ap-southeast-1.amazonaws.com/paddlepaddle.org:"$DOCKER_IMAGE_TAG"

if [[ ! -z $BUILD_TAG ]]
then
# For production builds, we also tag version, in case we need to revert
docker tag paddlepaddle.org:"$DOCKER_IMAGE_TAG" 330323714104.dkr.ecr.ap-southeast-1.amazonaws.com/paddlepaddle.org:"$BUILD_TAG"
docker push 330323714104.dkr.ecr.ap-southeast-1.amazonaws.com/paddlepaddle.org:"$BUILD_TAG"
fi

# deploy to remote server
openssl aes-256-cbc -d -a -in $TRAVIS_BUILD_DIR/scripts/travis/ubuntu.pem.enc -out ubuntu.pem -k $DEC_PASSWD

eval "$(ssh-agent -s)"
chmod 400 ubuntu.pem

ssh-add ubuntu.pem

ssh -i ubuntu.pem ubuntu@$STAGE_DEPLOY_IP << EOF
  set -e

  sudo bash
  eval $(aws ecr get-login --no-include-email --region ap-southeast-1)
  docker pull 330323714104.dkr.ecr.ap-southeast-1.amazonaws.com/paddlepaddle.org:${DOCKER_IMAGE_TAG}
  docker stop $DOCKER_CONTAINER_NAME
  docker rm $DOCKER_CONTAINER_NAME
  docker run --name=$DOCKER_CONTAINER_NAME -d -p $PORT:8000 -e ENV=$ENV -e SECRET_KEY=$SECRET_KEY -v /var/content:/var/content 330323714104.dkr.ecr.ap-southeast-1.amazonaws.com/paddlepaddle.org:$DOCKER_IMAGE_TAG
  docker image prune
EOF

chmod 644 ubuntu.pem
rm ubuntu.pem
