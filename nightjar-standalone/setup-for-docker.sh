#!/bin/sh

set -e

cd $( dirname "$0" )

test -e envoy-docker/src/.python-src && rm -r envoy-docker/src/.python-src
mkdir -p envoy-docker/src/.python-src
cp -R ../python-src/* envoy-docker/src/.python-src/.
