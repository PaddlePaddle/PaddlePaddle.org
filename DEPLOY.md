## Manual Deployment Instructions

**DEPENDENCIES:** 
* Make sure your local build machine has Docker and AWS CLI installed.  
* Make sure the remote VM also has Docker and AWS CLI installed.

##### Edit <PaddlePaddle_org_dir>/scripts/deploy.sh and modify the env variables

```
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
```

##### From <PaddlePaddle_org_dir> (where Dockerfile is), Execute deploy script

```
sh ./scripts/deploy.sh
```

## Continuous Integration using Travis-CI

PaddlePaddle.org integrates with Travis-CI to provide continuous deployments on commits to **"develop"**, **"release.\*"**, and tags with pattern **"^v\d+\.\d+(\.\d+)?(-\S\*)?$"**

| Environment | Push to branch/tag | Docker Image | Deploys to |
| ----------- |:------------------:|:------------:| ----------:|
Development | develop | <DOCKER_REPO>/paddlepaddle.org:develop | staging.paddlepaddle.org:82 |
Staging | release.\* | <DOCKER_REPO>/paddlepaddle.org:staging | staging.paddlepaddle.org:81 |
Production | master | <DOCKER_REPO>/paddlepaddle.org:(latest/\<TIMESTAMP\>) | staging.paddlepaddle.org |