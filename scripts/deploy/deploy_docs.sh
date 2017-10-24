#!/bin/bash
set -e

CONTENT_DEC_PASSWD=$1
SOURCE_DIR=$2
GITHUB_BRANCH=$3 # version

echo "1:($1) 2:($2) 3:($3)"

# debug use, this should be using develop or master on PPO
PPO_BRANCH=move_book_conversion_logic_to_PPO_script

# we are at the top level of PPO, we can `cd` to 'book', 'Paddle', 'models', '.ppo_workspace' ...
export CONTENT_DIR=$SOURCE_DIR/..
export DEPLOY_DOCS_DIR=$CONTENT_DIR/.ppo_workspace

[[ -d $DEPLOY_DOCS_DIR ]] || mkdir -p $DEPLOY_DOCS_DIR

if [[ $SOURCE_DIR == *"book"* ]]; then
    GENERATED_DOCS_DIR=$DEPLOY_DOCS_DIR/generated_docs/$GITHUB_BRANCH/book
    mkdir -p $GENERATED_DOCS_DIR

    CONTENT_DOCS_DIR=$DEPLOY_DOCS_DIR/content
    mkdir -p $CONTENT_DOCS_DIR

    CONVERT_BOOK_SH=https://raw.githubusercontent.com/PaddlePaddle/PaddlePaddle.org/$PPO_BRANCH/scripts/deploy/convert_md_to_html_for_book.sh
    curl $CONVERT_BOOK_SH | bash -s $SOURCE_DIR $GENERATED_DOCS_DIR
fi

#### pull PaddlePaddle.org app and run the deploy_documentation command
## https://github.com/PaddlePaddle/PaddlePaddle.org/archive/develop.zip

curl -LOk https://github.com/PaddlePaddle/PaddlePaddle.org/archive/$PPO_BRANCH.zip

unzip $PPO_BRANCH.zip

cd PaddlePaddle.org-$PPO_BRANCH/
cd portal/

sudo pip install -r requirements.txt

python manage.py deploy_documentation $GENERATED_DOCS_DIR $CONTENT_DOCS_DIR $GITHUB_BRANCH


## deploy to remote server
cd ../..
openssl aes-256-cbc -d -a -in PaddlePaddle.org-$PPO_BRANCH/scripts/deploy/content_mgr.pem.enc -out content_mgr.pem -k $CONTENT_DEC_PASSWD


eval "$(ssh-agent -s)"
chmod 400 content_mgr.pem

ssh-add content_mgr.pem
rsync -r $CONTENT_DOCS_DIR content_mgr@staging.paddlepaddle.org:/var/content2/.ppo_workspace

chmod 644 content_mgr.pem
