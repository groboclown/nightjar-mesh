#!/bin/bash

set -e

HERE=$( dirname "$0" )
WORK_DIR="${HERE}/../.work/envoy-api"
VENV_DIR="${HERE}/../.venv"
OUT_DIR="${HERE}/../src"

test -d "$WORK_DIR" || mkdir -p "$WORK_DIR"


test -d "${OUT_DIR}/envoy" && rm -rf "${OUT_DIR}/envoy"
mkdir -p "$OUT_DIR"
find "${VENV_DIR}/include" -name '*.proto' -print0 | xargs -0 \
  protoc \
    "--proto_path=${VENV_DIR}/include" \
    "--python_out=${OUT_DIR}"
find "${WORK_DIR}/envoy/api/envoy/api/v2" -name '*.proto' -print0 | xargs -0 \
  protoc \
    "--proto_path=${VENV_DIR}/include" \
    "--proto_path=${WORK_DIR}/envoy/api" \
    "--proto_path=${WORK_DIR}/protoc-gen-validate" \
    "--proto_path=${WORK_DIR}/googleapis" \
    "--python_out=${OUT_DIR}"
