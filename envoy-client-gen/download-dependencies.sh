#!/bin/bash

set -e

ENVOY_VERSION=1.12.2

cd $(dirname "$0")
BASE_TMP=$(pwd)/.tmp
PROTO_DIR="${BASE_TMP}/protos"
ENVOY_SRC_DIR="${BASE_TMP}/data-plane-api"
GOOGLEAPI_SRC_DIR="${BASE_TMP}/googleapis"
VALIDATE_SRC_DIR="${BASE_TMP}/protoc-gen-validate"
OPENCENSUS_SRC_DIR="${BASE_TMP}/opencensus-proto"
UDPA_SRC_DIR="${BASE_TMP}/udpa"


# Envoy protobuf sources
if [ ! -d "${ENVOY_SRC_DIR}" ] ; then
  ( cd "${BASE_TMP}" && git clone https://github.com/envoyproxy/data-plane-api.git )
else
  ( cd "${ENVOY_SRC_DIR}" && git pull )
fi

# Dependent sources
if [ ! -d "${GOOGLEAPI_SRC_DIR}" ] ; then
  ( cd "${BASE_TMP}" && git clone https://github.com/googleapis/googleapis.git )
else
  ( cd "${GOOGLEAPI_SRC_DIR}" && git pull )
fi

if [ ! -d "${VALIDATE_SRC_DIR}" ] ; then
  ( cd "${BASE_TMP}" && git clone https://github.com/envoyproxy/protoc-gen-validate.git )
else
  ( cd "${VALIDATE_SRC_DIR}" && git pull )
fi

if [ ! -d "${OPENCENSUS_SRC_DIR}" ] ; then
  ( cd "${BASE_TMP}" && git clone https://github.com/census-instrumentation/opencensus-proto.git )
else
  ( cd "${OPENCENSUS_SRC_DIR}" && git pull )
fi

if [ ! -d "${UDPA_SRC_DIR}" ] ; then
  ( cd "${BASE_TMP}" && git clone https://github.com/cncf/udpa.git )
else
  ( cd "${UDPA_SRC_DIR}" && git pull )
fi



# rsync -r --prune-empty-dirs src/.tmp/googleapis/ src/.tmp/proto-docker/protos --include='*/' --include='*.proto' --exclude='*'
#mkdir src/.tmp/proto-docker/protos/validate
#( cd src/.tmp/proto-docker/protos/validate && wget https://raw.githubusercontent.com/envoyproxy/protoc-gen-validate/master/validate/validate.proto )
#mkdir -p src/.tmp/proto-docker/protos/opencensus/proto/trace/v1
#( cd src/.tmp/proto-docker/protos/opencensus/proto/trace/v1 && wget https://raw.githubusercontent.com/census-instrumentation/opencensus-proto/master/src/opencensus/proto/trace/v1/trace_config.proto )
#( cd src/.tmp/proto-docker/protos/opencensus/proto/trace/v1 && wget https://raw.githubusercontent.com/census-instrumentation/opencensus-proto/master/src/opencensus/proto/trace/v1/trace.proto )
#mkdir -p src/.tmp/proto-docker/protos/opencensus/proto/resource/v1
#( cd src/.tmp/proto-docker/protos/opencensus/proto/resource/v1 && wget https://raw.githubusercontent.com/census-instrumentation/opencensus-proto/master/src/opencensus/proto/resource/v1/resource.proto )
