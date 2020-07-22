#!/bin/bash

src_file=/tmp/$$-requirements.txt
unversioned=/tmp/$$-unversioned.txt
cd $( dirname "$0" )
cat ../test-requirements.txt ../*/requirements.txt | sort | uniq > "$src_file"
cat "$src_file" | cut -f 1 -d ' ' | cut -f 1 -d '>' | cut -f 1 -d '<' | cut -f 1 -d '=' | sort | uniq > "$unversioned"
src_count=$( cat "$src_file" | wc --lines )
unversioned_count=$( cat "$unversioned" | wc --lines )
rm "$src_file" "$unversioned"
if [ $src_count -ne $unversioned_count ] ; then
  echo "There exist required modules with conflicting version specifications."
  echo "Requirements files: FAIL" >&2
  exit 1
fi
echo "Requirements files: OK" >&2
