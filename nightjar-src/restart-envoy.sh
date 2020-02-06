#!/bin/sh

if [ ! -z "$ENVOY_LOG_LEVEL" ] ; then
  ENVOY_CMD="envoy --log-level $ENVOY_LOG_LEVEL"
else
  ENVOY_CMD="envoy"
fi

config_file="$1"

if [ -f /tmp/envoy.pid ] ; then
  echo "Stopping envoy."
  /bin/kill -term $( cat /tmp/envoy.pid )
  # Should properly wait for envoy to stop, but instead we just wait a bit.
  sleep 1
fi
echo "Starting envoy."
$ENVOY_CMD -c "$config_file" &
echo $! > /tmp/envoy.pid
