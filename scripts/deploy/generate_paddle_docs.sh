#!/bin/bash
set -e

DOCS_LOCATION=$1
DESTINATION_DIR=$2

echo "Generating paddle documentation at $DOCS_LOCATION to $DESTINATION_DIR"
cd "$DOCS_LOCATION"

# Create the build directory for CMake.
mkdir -p $DOCS_LOCATION/ppo_build
cd $DOCS_LOCATION/ppo_build

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

# Disable paddle fluid and paddle operators docs for now, since the build does not currently work
# TODO[thuan]: Make document generator work with paddle fluid and paddle operators docs

# Compile Documentation only.
cmake "$DOCS_LOCATION" -DCMAKE_BUILD_TYPE=Release -DWITH_GPU=OFF -DWITH_MKL=OFF -DWITH_DOC=ON -DWITH_STYLE_CHECK=OFF
make -j $processors gen_proto_py framework_py_proto
make -j $processors copy_paddle_pybind

export PYTHONPATH=$DOCS_LOCATION/ppo_build/python
