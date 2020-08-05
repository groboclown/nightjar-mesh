# Docker Container: Central

Container that pulls the discovery-map for the mesh document, then commits it to the data store.

## Usage

```bash
TRIGGER_STOP_FILE=/tmp/stop.txt
REFRESH_TIME=30
FAILURE_SLEEP=300
EXIT_ON_GENERATION_FAILURE=false
NJ_TEMP_DIR=/tmp/dir

# And, as required...
DATA_STORE_EXEC=???
DISCOVERY_MAP_EXEC=???

# If set to 'true', then debug logging is enabled
DEBUG=false
```
