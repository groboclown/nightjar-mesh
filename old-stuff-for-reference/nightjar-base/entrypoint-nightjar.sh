#!/bin/sh

export PYTHONPATH="/nightjar-src/python-src:${PYTHONPATH}"

if [ "$DEBUG_CONTAINER" = 1 ] ; then
  exec /bin/sh "$@"
fi

cd /nightjar-src
exec /bin/sh ./entrypoint.sh
