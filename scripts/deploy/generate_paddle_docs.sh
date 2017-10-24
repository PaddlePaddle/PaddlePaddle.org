#!/bin/bash
set -e

DOCS_LOCATION=$1
DESTINATION_DIR=$2

echo "Generating paddle documentation at $DOCS_LOCATION"
cd "$DOCS_LOCATION"

find . -name "CMakeCache.txt" -exec rm -R {} \;

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
cmake "$DOCS_LOCATION" -DCMAKE_BUILD_TYPE=Debug -DWITH_GPU=OFF -DWITH_MKLDNN=OFF -DWITH_MKLML=OFF -DWITH_DOC=ON
make -j $processors gen_proto_py
make -j $processors paddle_docs paddle_docs_cn

cp -r $DOCS_LOCATION/doc/cn $DESTINATION_DIR/.
cp -r $DOCS_LOCATION/doc/en $DESTINATION_DIR/.