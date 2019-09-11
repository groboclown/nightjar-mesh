#!/bin/bash

set -e

PROTOBUF_VERSION=3.9.1

# Create the Python virtual environment for developing nightjar.

HERE=$( dirname "$0" )
TMP_DIR="${HERE}/../.work/protobuf.tmp"
WORK_DIR="${HERE}/../.work/protobuf"
VENV_DIR="${HERE}/../.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "You must setup the development environment first (${HERE}/mk-dev-venv.sh)"
  exit 1
fi
source "$VENV_DIR/bin/activate"

# Protobuf stuff...
mkdir -p "$WORK_DIR"
mkdir -p "$TMP_DIR"

if [ ! -d "${WORK_DIR}/protobuf-python" ]; then
  if [ ! -f "${TMP_DIR}/protobuf-python-${PROTOBUF_VERSION}.zip" ]; then
    curl -L --output "${TMP_DIR}/protobuf-python-${PROTOBUF_VERSION}.zip" \
      "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOBUF_VERSION}/protobuf-python-${PROTOBUF_VERSION}.zip"
  fi
  test -d "${TMP_DIR}/protobuf-python" && rm -rf "${TMP_DIR}/protobuf-python"
  unzip "${TMP_DIR}/protobuf-python-${PROTOBUF_VERSION}.zip" -d "${TMP_DIR}/protobuf-python"
  mv "${TMP_DIR}/protobuf-python/protobuf-${PROTOBUF_VERSION}/python" "${WORK_DIR}/protobuf-python"
  ( cd "${WORK_DIR}/protobuf-python" && python setup.py test )
fi

if [ ! -x "${VENV_DIR}/bin/protoc" ]; then
  # TODO detect the arch to download
  if [ ! -f "${TMP_DIR}/protoc-${PROTOBUF_VERSION}-linux-x86_64.zip" ]; then
    curl -L --output "${TMP_DIR}/protoc-${PROTOBUF_VERSION}-linux-x86_64.zip" \
      "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOBUF_VERSION}/protoc-${PROTOBUF_VERSION}-linux-x86_64.zip"
  fi
  unzip -n "${TMP_DIR}/protoc-${PROTOBUF_VERSION}-linux-x86_64.zip" -d "${VENV_DIR}" > /dev/null
fi

test -d "${WORK_DIR}/envoy" || ( cd "$WORK_DIR" && git clone --depth 1 https://github.com/envoyproxy/envoy.git )
( cd "$WORK_DIR/envoy" && git fetch --depth 1 )
test -d "${WORK_DIR}/protoc-gen-validate" || ( cd "${WORK_DIR}" && git clone --depth 1 https://github.com/envoyproxy/protoc-gen-validate.git )
( cd "${WORK_DIR}/protoc-gen-validate" && git fetch --depth 1 )
test -d "${WORK_DIR}/googleapis" || ( cd "${WORK_DIR}" && git clone --depth 1 https://github.com/googleapis/googleapis.git )
( cd "${WORK_DIR}/googleapis" && git fetch --depth 1 )
