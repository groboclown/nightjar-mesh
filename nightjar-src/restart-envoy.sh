#!/bin/sh

config_file="$1"

# If envoy is not running AND we have a configuration file, start it.
if [ -f "${config_file}" ] ; then
  envoy_pid=
  if [ -f "${ENVOY_PID_FILE}" ] ; then
    envoy_pid=$( cat "${ENVOY_PID_FILE}" )
  fi
  kill -0 ${envoy_pid} >/dev/null 2>&1
  if [ $? -ne 0 ] ; then
    envoy --log-level ${ENVOY_LOG_LEVEL} -c "${config_file}"
  fi
fi
