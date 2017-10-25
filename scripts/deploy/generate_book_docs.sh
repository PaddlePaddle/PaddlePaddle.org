#!/bin/bash
set -e

DOCS_LOCATION=$1
DESTINATION_DIR=$2

echo "Generating paddle book at $DOCS_LOCATION to $DESTINATION_DIR"
cd "$DOCS_LOCATION"

if [ ! -d "$DESTINATION_DIR" ]; then
    echo "Directory $DESTINATION_DIR does not exists, creating..."
    mkdir -p $DESTINATION_DIR
fi

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
      mkdir $DESTINATION_DIR/$i
      mv $i/index.html $DESTINATION_DIR/$i
      mv $i/index.cn.html $DESTINATION_DIR/$i
      cp -r $i/image $DESTINATION_DIR/$i
    fi

done
