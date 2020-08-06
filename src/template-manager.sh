#!/bin/sh

pushd $( dirname "$0" ) > /dev/null 2>&1
_HERE=$(pwd)
popd > /dev/null 2>&1
export PYTHONPATH="${_HERE}/py-tool-template-manager:${_HERE}/py-common"
python3 -m nightjar_template_manager "$@"
