#!/bin/bash

set -e

_here=$( dirname "$0" )
for n in "${_here}"/py-* ; do
  if [ -d "$n" ] ; then
    i=$( basename "$n" )
    "$@" $i
  fi
done
