#!/bin/bash

set -e

PROTOBUF_VERSION=3.9.1

# Create the Python virtual environment for developing nightjar.

HERE=$( dirname "$0" )
WORK_DIR="${HERE}/../.work/protobuf"
VENV_DIR="${HERE}/../.venv"

test -d "$VENV_DIR" || ( mkdir -p "$VENV_DIR" && cd "$VENV_DIR" && python3 -m venv .)

source "$VENV_DIR/bin/activate"

pip3 install -r "$HERE/../requirements.txt"
pip3 install -r "$HERE/../dev-requirements.txt"
