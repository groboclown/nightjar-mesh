#!/bin/sh

if [ "$DEBUG_CONTAINER" = 1 ] ; then
  exec /bin/sh
fi

tr -d '\015' < /nightjar/run-loop.sh > /tmp/run-loop.sh
chmod +x /tmp/run-loop.sh
exec /tmp/run-loop.sh
