#!/bin/bash
set -e

DOCS_LOCATION=$1
DESTINATION_DIR=$2
LANGUAGE=$3

echo "Generating visualdl documentation at $DOCS_LOCATION to $DESTINATION_DIR"
cd "$DOCS_LOCATION"

# Create the build directory for CMake.
mkdir -p $DOCS_LOCATION/build
cd $DOCS_LOCATION/build

if [ ! -d "$DESTINATION_DIR" ]; then
    echo "Directory $DESTINATION_DIR does not exists, creating..."
    mkdir -p $DESTINATION_DIR
fi

processors=1
if [ "$(uname)" == "Darwin" ]; then
    processors=`sysctl -n hw.ncpu`
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    processors=`nproc`
fi

# Compile Documentation only.
cmake "$DOCS_LOCATION" -DWITH_DOC=ON


mkdir -p $DESTINATION_DIR

if [ "$LANGUAGE" == "en" ]; then
    make -j $processors visualdl_docs_en
    cp -r $DOCS_LOCATION/build/docs/en/html $DESTINATION_DIR/.

elif if [ "$LANGUAGE" == "zh" ]; then
    make -j $processors visualdl_docs_cn
    cp -r $DOCS_LOCATION/build/docs/cn/html $DESTINATION_DIR/.

else
    make -j $processors visualdl_docs_en visualdl_docs_cn
    cp -r $DOCS_LOCATION/build/docs/en/html $DESTINATION_DIR/visualdl/en/develop/.
    cp -r $DOCS_LOCATION/build/docs/cn/html $DESTINATION_DIR/visualdl/zh/develop/.
fi
