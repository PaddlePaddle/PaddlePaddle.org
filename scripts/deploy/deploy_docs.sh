#!/bin/bash
set -e

DEC_PASSWD=$1
GITHUB_BRANCH=$2
SOURCE_DIR=$3

echo "1:($1) 2:($2) 3:($3) 4:($4)"

# Pull PaddlePaddle.org app and run the deploy_documentation command
PPO_BRANCH=new-contribibutor-experience

curl -LOk https://github.com/PaddlePaddle/PaddlePaddle.org/archive/$PPO_BRANCH.zip
unzip $PPO_BRANCH.zip
cd PaddlePaddle.org-$PPO_BRANCH/portal
sudo pip install --ignore-installed -r requirements.txt

mkdir $DESTINATION_DIR
python manage.py deploy_documentation --source_dir=$SOURCE_DIR --destination_dir=documentation $GITHUB_BRANCH

# Deploy to remote server by SSH'ing into it.
openssl aes-256-cbc -d -a -in ../scripts/deploy/content_mgr.pem.enc -out content_mgr.pem -k $DEC_PASSWD
eval "$(ssh-agent -s)"
chmod 400 content_mgr.pem
ssh-add content_mgr.pem
export STAGE_DEPLOY_IP=13.229.163.131

rsync -r documentation content_mgr@$STAGE_DEPLOY_IP:/var/www/portal/documentation
rsync -r menus content_mgr@$STAGE_DEPLOY_IP:/var/www/portal/menus

chmod 644 content_mgr.pem
rm -rf documentation
rm -rf menus
