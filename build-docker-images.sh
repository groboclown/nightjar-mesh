#!/bin/sh

LOCAL_REPOSITORY_NAME=${LOCAL_REPOSITORY_NAME:=local}
if [ ! -z "$1" ] ; then
    LOCAL_REPOSITORY_NAME="$1"
fi

cd $( dirname "$0" )

# The base images MUST be named "local"
(
  cd nightjar-base && \
  docker build -t local/nightjar-base-alpine -f Dockerfile.alpine . && \
  docker build -t local/nightjar-base-envoy -f Dockerfile.envoy .
) || exit 1

(
  cd nightjar-central/envoy-docker && \
  docker build -t ${LOCAL_REPOSITORY_NAME}/nightjar-central-envoy .
) || exit 1

(
  cd nightjar-central/configurator-docker && \
  docker build -t ${LOCAL_REPOSITORY_NAME}/nightjar-central-configurator .
) || exit 1

(
  cd nightjar-standalone/envoy-docker && \
  docker build -t ${LOCAL_REPOSITORY_NAME}/nightjar-standalone .
) || exit 1
