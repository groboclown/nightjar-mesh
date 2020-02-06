#!/bin/sh

# Polls from the proxy generator to see if it needs to restart the Envoy proxy.

# This runs as a minimal permission user, so writing to the file system
# must be done under /tmp

cd $( dirname $0 )

REFRESH_TIME=${REFRESH_TIME:=10}
FAILURE_SLEEP=${FAILURE_SLEEP:=300}
EXIT_ON_GENERATION_FAILURE=${EXIT_ON_GENERATION_FAILURE:=0}
ENVOY_CONFIGURATION_TEMPLATE=${ENVOY_CONFIGURATION_TEMPLATE:=./envoy.yaml.mustache}


test -f /tmp/stop.txt && rm /tmp/stop.txt
while [ ! -f /tmp/stop.txt ] ; do
  # Generate the envoy config file
  /bin/sh ./generate-envoy-yaml.sh /tmp/new-envoy.yaml
  if [ $? -ne 0 ] ; then
    if [ $EXIT_ON_GENERATION_FAILURE -ne 0 ] ; then
      echo "Waiting before exiting to allow debugging."
      sleep $FAILURE_SLEEP
      exit 1
    fi
  else
    diff /tmp/envoy-config.yaml /tmp/new-envoy.yaml > /dev/null 2>&1
    if [ $? -ne 0 ] ; then
      echo "New envoy file differs from old one."
      cp /tmp/new-envoy.yaml /tmp/enovy-config.yaml
      /bin/sh ./restart-envoy.sh /tmp/envoy-config.yaml
    fi
  fi
  test -f /tmp/new-envoy.yaml && rm /tmp/new-envoy.yaml
  sleep ${REFRESH_TIME}
done
