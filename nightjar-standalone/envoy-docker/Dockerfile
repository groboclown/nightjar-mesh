FROM local/nightjar-base-envoy:latest

# This assumes that the .sh files have the correct Unix line-endings on your system
# before running.

# Expose the default admin port and default service port.
EXPOSE 9901 8080

ENV ENVOY_ADMIN_PORT 9901
ENV SERVICE_PORT 8080
ENV SERVICE_MEMBER NOT_SET
ENV SERVICE_CONTAINER_NAME NOT_SET

copy nightjar-src/ /nightjar-src/
