# Docker Container: Standalone

Container that pulls from the discovery-map to get the mesh document, pulls templates from the data store, merges the two together, and manages the Envoy proxy process.

## Usage

```bash
NJ_PROXY_MODE=service
ENVOY_EXEC=/usr/local/bin/envoy
ENVOY_LOG_LEVEL=info
ENVOY_BASE_ID=0
ENVOY_CONFIGURATION_TEMPLATE=envoy-config.yaml
ENVOY_CONFIGURATION_DIR=/tmp/envoy/
TRIGGER_STOP_FILE=/tmp/stop.txt
REFRESH_TIME=30
FAILURE_SLEEP=300
EXIT_ON_GENERATION_FAILURE=false

# And, as required...
DATA_STORE_EXEC=???
DISCOVERY_MAP_EXEC=???
NJ_LISTEN_PORT=3000
NJ_ADMIN_PORT=9901

# Optional; see standard-usage.md
NJ_NAMESPACE=???
NJ_SERVICE=???
NJ_COLOR=???

# If set to 'true', then debug logging is enabled
DEBUG=false
```
