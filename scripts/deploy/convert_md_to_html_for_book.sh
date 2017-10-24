#!/bin/bash
function abort(){
    echo "Cannot convert markdown to html in book repo" 1>&2
    exit 1
}

SOURCE_DIR=$1
DEPLOY_DOCS_DIR=$2

echo "convert md to html for book to $SOURCE_DIR => $DEPLOY_DOCS_DIR"


CURRENT_DIR=`pwd`


trap 'abort' 0

cd $SOURCE_DIR/


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

done

trap : 0

