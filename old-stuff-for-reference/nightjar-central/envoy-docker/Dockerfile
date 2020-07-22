FROM local/nightjar-base-alpine:latest

# This assumes that the .sh files have the correct Unix line-endings on your system
# before running.

# This file is broken into chunks to allow faster build times
# if you modify the source files.

# Expose the default admin port and default service port.
EXPOSE 9901 8080

COPY nightjar-src/ /nightjar-src/
