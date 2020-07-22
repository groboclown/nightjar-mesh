#!/bin/sh

# Run the python script directly.  This has the added benefit of sending
# signals directed at the docker container to the python executable.
exec python3 -m nightjar.entry.central_configurator
