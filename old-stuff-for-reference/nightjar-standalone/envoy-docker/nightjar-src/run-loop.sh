#!/bin/sh

# Polls from the proxy generator to see if it needs to restart the Envoy proxy.

# This runs as a minimal permission user, so writing to the file system
# must be done under /tmp.

# This file, like all the executable code in nightjar, is designed to be testable.

cd $( dirname $0 )

# Global across scripts
export ENVOY_PID_FILE=${ENVOY_PID_FILE:=/tmp/envoy.pid}
export ENVOY_LOG_LEVEL=${ENVOY_LOG_LEVEL:=info}
export TMP_DIR=${TMP_DIR:=/tmp}
export ENVOY_BASE_ID=${ENVOY_BASE_ID:=0}

# Local to this file
REFRESH_TIME=${REFRESH_TIME:=30}
FAILURE_SLEEP=${FAILURE_SLEEP:=300}
EXIT_ON_GENERATION_FAILURE=${EXIT_ON_GENERATION_FAILURE:=0}
ENVOY_TEMPLATE_DIR=${ENVOY_TEMPLATE_DIR:=./templates}
ENVOY_CONFIGURATION_FILE=${ENVOY_CONFIGURATION_TEMPLATE:=envoy-config.yaml}
TRIGGER_STOP_FILE=${TRIGGER_STOP_FILE:=/tmp/stop.txt}

# Prevent everything calling AWS resources at the same time by introducing
# a small, random back-off once at the start.  This is a 0-7 second period.
# Doing this once prevents an eventual evening out, which would happen if
# we did it in the while loop.
# However, this is considered to be too drastic.  It puts a possibly unnecessary
# and costly (in terms of availability time) addition that should work itself
# out by the internal throttling logic of the data generation tool.
# sleep $(( RANDOM & 7 ))

test -f "${TRIGGER_STOP_FILE}" && rm "${TRIGGER_STOP_FILE}"
mkdir -p "${TMP_DIR}/active-envoy-config"
while [ ! -f "${TRIGGER_STOP_FILE}" ] ; do
  # Generate the envoy config file
  /bin/sh ./generate-envoy-yaml.sh "${ENVOY_TEMPLATE_DIR}" "${TMP_DIR}/envoy-new-config"
  if [ $? -ne 0 ] ; then
    if [ ${EXIT_ON_GENERATION_FAILURE} -ne 0 ] ; then
      echo "Waiting before exiting to allow debugging."
      sleep ${FAILURE_SLEEP}
      exit 1
    fi
  elif [ -d "${TMP_DIR}/envoy-new-config" ] ; then
    # This MUST be a move operation; envoy proxy only reloads on moves.
    mv "${TMP_DIR}/envoy-new-config"/* "${TMP_DIR}/active-envoy-config/".
  fi
  /bin/sh ./restart-envoy.sh "${TMP_DIR}/active-envoy-config/${ENVOY_CONFIGURATION_FILE}"
  sleep ${REFRESH_TIME}
done
