FROM local/nightjar-base-alpine:latest

# This assumes that the .sh files have the correct Unix line-endings on your system
# before running.

ENV SERVICE_PORT 8080
ENV SERVICE_MEMBER NOT_SET
ENV SERVICE_CONTAINER_NAME NOT_SET

VOLUME /tmp/active-envoy-config

copy nightjar-src/ /nightjar-src/

# Example envoy startup:
# "--config", "{node:{id:${SERVICE_MEMBER},cluster:${SERVICE_CONTAINER_NAME}},admin:{access_log_path:/dev/stdout,address:{socket_address:{address:0.0.0.0,port_value:${ENVOY_ADMIN_PORT}}}},dynamic_resources:{cds_config:{path:/mnt/envoy-config/active-envoy-config/cds.yaml},lds_config:{path:/mnt/envoy-config/active-envoy-config/lds.yaml}}"
