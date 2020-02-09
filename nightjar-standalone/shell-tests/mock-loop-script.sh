#!/bin/sh

count=$( cat ${SUCCESS_FILE3} )
count=$(( $count + 1 ))
echo "${count}" > ${SUCCESS_FILE3}
echo "${MOCK_DATA3}" > /tmp/new-envoy.yaml

if [ $count -ge "$MAX_COUNT" ] ; then
  touch /tmp/stop.txt
fi

exit ${MOCK_EXIT_CODE3:=0}
