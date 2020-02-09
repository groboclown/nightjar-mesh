#!/bin/sh

if [ "$DEBUG_CONTAINER" = 1 ] ; then
  exec /bin/sh "$@"
fi

cd /nightjar-src
exec /bin/sh ./run-loop.sh
