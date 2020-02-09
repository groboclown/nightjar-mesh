#!/bin/sh

config_file="$1"

# If envoy is not running AND we have a configuration file, start it.
if [ -f "${config_file}" ] ; then
  envoy_pid=
  if [ -f "${ENVOY_PID_FILE}" ] ; then
    envoy_pid=$( cat "${ENVOY_PID_FILE}" )
  fi
  # If we don't have a PID, or if the pid is not a valid process ID,
  # then `kill` will have a non-zero exit code.  Kill with signal 0
  # just asks `kill` if the process ID exists.
  # Note that this uses the executable kill, and not the shell kill.
  # This is to allow easier testing.
  /bin/kill -0 ${envoy_pid} >/dev/null 2>&1
  if [ $? -ne 0 ] ; then
    echo "Envoy not running on pid ${envoy_pid}"
    envoy --log-level ${ENVOY_LOG_LEVEL} -c "${config_file}" --base-id ${ENVOY_BASE_ID} &
    echo $! > "${ENVOY_PID_FILE}"
    echo "Started envoy on pid $( cat ${ENVOY_PID_FILE} )"
  fi
fi
