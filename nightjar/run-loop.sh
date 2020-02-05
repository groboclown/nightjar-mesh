#!/bin/sh

# Polls from the proxy generator to see if it needs to restart the Envoy proxy.

REFRESH_TIME=${REFRESH_TIME:=10}
FAILURE_SLEEP=${FAILURE_SLEEP:=300}
EXIT_ON_GENERATION_FAILURE=${EXIT_ON_GENERATION_FAILURE:=0}

if [ ! -z "$ENVOY_LOG_LEVEL" ] ; then
  ENVOY_CMD="envoy --log-level $ENVOY_LOG_LEVEL"
else
  ENVOY_CMD="envoy"
fi


test -f /tmp/stop.txt && rm /tmp/stop.txt
while [ ! -f /tmp/stop.txt ] ; do
  # Generate the envoy file
  echo "Generating the new envoy file."
  python3 /nightjar/generate-proxy-file.py > /tmp/new-envoy.yaml
  if [ $? -ne 0 ] ; then
    echo "Failed to generate proxy file."
    if [ $EXIT_ON_GENERATION_FAILURE -ne 0 ] ; then
      echo "Waiting before exiting to allow debugging."
      sleep $FAILURE_SLEEP
      exit 1
    fi
  else
    diff /tmp/envoy-1.yaml /tmp/new-envoy.yaml > /dev/null 2>&1
    if [ $? -ne 0 ] ; then
      echo "New envoy file differs from old one."
      # This is really weird.  The /tmp/envoy.yaml file is shown in
      # directory listing, but can't be accessed.
      cp /tmp/new-envoy.yaml /tmp/enovy.yaml
      # So this additional copy makes a version that can be used.
      cp /tmp/new-envoy.yaml /tmp/envoy-1.yaml
      if [ -f /tmp/envoy.pid ] ; then
        echo "Stopping envoy."
        kill -term $( cat /tmp/envoy.pid )
        # SHould properly wait for envoy to stop, but instead we just wait a bit.
        sleep 1
      fi
      echo "Starting envoy."
      $ENVOY_CMD -c /tmp/envoy-1.yaml &
      echo $! > /tmp/envoy.pid
    fi
  fi
  test -f /tmp/new-envoy.yaml && rm /tmp/new-envoy.yaml
  sleep ${REFRESH_TIME}
done
