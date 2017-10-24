#!/bin/bash

SOURCE_DIR=$1
DEPLOY_DOCS_DIR=$2

echo "convert md to html for book to $SOURCE_DIR => $DEPLOY_DOCS_DIR"


CURRENT_DIR=`pwd`


if [[ "$TRAVIS_BRANCH" =~ ^v[[:digit:]]+\.[[:digit:]]+(\.[[:digit:]]+)?(-\S*)?$ ]]
then
    # Production Deploy
    echo "Deploying to PROD"
elif [ "$TRAVIS_BRANCH" == "develop" ]
then
    # Development Deploy
    echo "Deploying to DEVELOP"
else
    # All other branches should be ignored
    echo "Cannot deploy image, invalid branch: $TRAVIS_BRANCH"
    exit 1
fi

trap 'abort' 0

cd book/

cp -r .tools/ $DEPLOY_DOCS_DIR/.tools

for i in `ls -F | grep /` ; do
    should_convert_and_copy=false
    cd $i

    if [ -e README.md ] && [ -e README.cn.md ] && [ -d image ]
    then
        should_convert_and_copy=true
    fi

    cd ..

    if $should_convert_and_copy ; then
      python .pre-commit-hooks/convert_markdown_into_html.py $i/README.md
      python .pre-commit-hooks/convert_markdown_into_html.py $i/README.cn.md
      mkdir $DEPLOY_DOCS_DIR/$i
      mv $i/index.html $DEPLOY_DOCS_DIR/$i
      mv $i/index.cn.html $DEPLOY_DOCS_DIR/$i
      cp -r $i/image $DEPLOY_DOCS_DIR/$i
    fi

    python .tools/convert_jinja2_into_html.py .tools/templates/index.html.json
    python .tools/convert_jinja2_into_html.py .tools/templates/index.cn.html.json

    mv .tools/templates/index.html $DEPLOY_DOCS_DIR/
    mv .tools/templates/index.cn.html $DEPLOY_DOCS_DIR/

done

trap : 0

