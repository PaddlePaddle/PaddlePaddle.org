#!/bin/bash
set -e

CONTENT_DEC_PASSWD=$1
SOURCE_DIR=$2
GITHUB_BRANCH=$3 # version

echo "1:($1) 2:($2) 3:($3)"

PPO_BRANCH=move_book_conversion_logic_to_PPO_script # debug

# we are at the top level of PPO, we can `cd` to 'book', 'Paddle', 'models', '.ppo_workspace' ...
export CONTENT_DIR=`pwd`/$SOURCE_DIR
export DEPLOY_DOCS_DIR=`pwd`/.ppo_workspace

[[ -d $DEPLOY_DOCS_DIR ]] || mkdir $DEPLOY_DOCS_DIR

 #TODO: Set GENERATED_DOCS DIR: ie: /.ppo_workspace/generated_docs/book

if [[ $SOURCE_DIR == *"book"* ]]; then
    mkdir -p $DEPLOY_DOCS_DIR/generated_docs/book/$GITHUB_BRANCH
    GENERATED_DOCS_DIR=$DEPLOY_DOCS_DIR/generated_docs/book/$GITHUB_BRANCH
    CONVERT_BOOK_SH=https://raw.githubusercontent.com/PaddlePaddle/PaddlePaddle.org/$PPO_BRANCH/scripts/deploy/convert_md_to_html_for_book.sh
    curl $CONVERT_BOOK_SH | bash -s $SOURCE_DIR $GENERATED_DOCS_DIR
fi

exit
# TODO:  Call HTML generation code for book, model, and Paddle/doc.  Copy generated HTML
# to .ppo_workspace/generated_docs

#
#
# if [ -d $DEPLOY_DOCS_DIR/generated_docs/book ]
# then
#     rm -rf $DEPLOY_DOCS_DIR/generated_docs/book
# fi


#
#### pull PaddlePaddle.org app and run the deploy_documentation command
## https://github.com/PaddlePaddle/PaddlePaddle.org/archive/develop.zip
#


curl -LOk https://github.com/PaddlePaddle/PaddlePaddle.org/archive/$PPO_BRANCH.zip
#
unzip $PPO_BRANCH.zip
#
cd PaddlePaddle.org-$PPO_BRANCH/
# #
cd portal/
#
sudo pip install -r requirements.txt
#
#mkdir ./tmp
python manage.py deploy_documentation $CONTENT_DIR $GENERATED_DOCS_DIR $GITHUB_BRANCH
#
#
## deploy to remote server
#openssl aes-256-cbc -d -a -in ../scripts/deploy/content_mgr.pem.enc -out content_mgr.pem -k $DEC_PASSWD
#
#
#eval "$(ssh-agent -s)"
#chmod 400 content_mgr.pem
#
#
#ssh-add content_mgr.pem
#rsync -r $DEPLOY_DOCS_DIR/content/docs content_mgr@52.76.173.135:/var/content/docs
#
#
#chmod 644 content_mgr.pem
#
#rm -rf $DEPLOY_DOCS_DIR
