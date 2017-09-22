#!/bin/bash
set -e

# THESE VARIABLES ARE DEFINED ON TRAVIS JOB
export AWS_ACCESS_KEY_ID="<YOUR_AWS_ACCESS_KEY>"
export AWS_SECRET_ACCESS_KEY="<YOUR_AWS_SECRET_ACCESS_KEY>"
export DEC_PASSWD="<PASSWORD_TO_DECODE_PEM_ENC_FILE"
export PROD_DEPLOY_IP="<PRODUCTION_SERVER_IP>"
export STAGE_DEPLOY_IP="<STAGE_DEV_SERVER_IP>"
export SECRET_KEY="<SERVER_SECRET>"

# THESE VARIABLES ARE GIVEN BY TRAVIS CI DURING BUILD
export TRAVIS_BRANCH="develop"  # options are master (prod), develop (development), release (staging)
export TRAVIS_BUILD_DIR="<LOCAL_PADDLEPADDLE_ORG_SRC_DIR>"

# SET THIS TO 1 if you want to skip awscli install
export SKIP_INSTALL="1"

./scripts/travis/build-docker.sh
./scripts/travis/deploy-image.sh
