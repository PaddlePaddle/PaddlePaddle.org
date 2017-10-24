#!/bin/bash
set -e

DEC_PASSWD=$1
GITHUB_BRANCH=$2
SOURCE_DIR=$3
GENERATED_DOCS_DIR=$4

echo "1:($1) 2:($2) 3:($3) 4:($4)"

# CONTENT_DIR ENV variable is required by PPO 'deploy_documentation' command
export CONTENT_DIR=$SOURCE_DIR/..
DEPLOY_DOCS_DIR=$CONTENT_DIR/.ppo_workspace


### pull PaddlePaddle.org app and run the deploy_documentation command
# https://github.com/PaddlePaddle/PaddlePaddle.org/archive/develop.zip

curl -LOk https://github.com/PaddlePaddle/PaddlePaddle.org/archive/develop.zip

unzip develop.zip

cd PaddlePaddle.org-develop/

cd portal/

sudo pip install -r requirements.txt

mkdir ./tmp
python manage.py deploy_documentation --source=$SOURCE_DIR --dest_gen_docs_dir=$GENERATED_DOCS_DIR --doc_version=$GITHUB_BRANCH


# deploy to remote server
openssl aes-256-cbc -d -a -in ../scripts/deploy/content_mgr.pem.enc -out content_mgr.pem -k $DEC_PASSWD


eval "$(ssh-agent -s)"
chmod 400 content_mgr.pem


ssh-add content_mgr.pem
rsync -r $DEPLOY_DOCS_DIR/content/docs content_mgr@52.76.173.135:/var/content/.ppo_workspace/content/docs


chmod 644 content_mgr.pem

rm -rf $DEPLOY_DOCS_DIR
