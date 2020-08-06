#!/bin/sh

pushd $( dirname "$0" ) > /dev/null 2>&1
_HERE=$(pwd)
popd > /dev/null 2>&1
for i in "${_HERE}"/* ; do
  if [ -d "$i" ] ; then
    export PYTHONPATH="${PYTHONPATH}:${i}"
  fi
done
python3 -m nightjar_template_manager "$@"
