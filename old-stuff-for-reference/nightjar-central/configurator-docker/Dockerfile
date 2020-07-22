FROM local/nightjar-base-envoy:latest

# This assumes that the .sh files have the correct Unix line-endings on your system
# before running.

# This file is broken into chunks to allow faster build times
# if you modify the source files.

# Expose the default admin port and service port.
EXPOSE 9901 8080

ENV ENVOY_ADMIN_PORT 9901
ENV SERVICE_PORT 8080
ENV SERVICE_MEMBER NOT_SET
ENV SERVICE_CONTAINER_NAME NOT_SET

COPY nightjar-src/ /nightjar-src/
