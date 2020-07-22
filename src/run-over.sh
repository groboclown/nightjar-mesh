#!/bin/bash

set -e

cd $( dirname "$0" )
for i in py-* ; do
  if [ -d "$i" ] ; then
    "$@" $i
  fi
done
