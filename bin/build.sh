#!/bin/bash

set -e

cd $( dirname "$0" )/..


docker build -t $USER/nightjar-build -f Dockerfile.build .
docker rm $USER-nightjar-build || echo "(No existing build container)"
docker run -it --name $USER-nightjar-build $USER/nightjar-build
test -d dist || mkdir -p dist
docker cp $USER-nightjar-build:/nightjar-mesh dist/nightjar-mesh
docker rm $USER-nightjar-build || echo "(No existing build container)"
