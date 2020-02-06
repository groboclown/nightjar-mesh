FROM envoyproxy/envoy-alpine:v1.13.0

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

COPY nightjar-src/requirements.txt /tmp/requirements.txt
RUN echo "start" \
    && apk upgrade \
    && apk add --update python3 curl \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && mv /etc/envoy/envoy.yaml /etc/envoy/envoy-example.yaml \
    && echo "end"

COPY nightjar-src/ /nightjar-src/
COPY entrypoint-nightjar.sh /entrypoint-nightjar.sh
COPY LICENSE /nightjar-LICENSE

# Rather than add another layer to "chmod +x" the necessary files,
# we just explicitly run /bin/sh and python3.

# This is to test the .dockerignore, to keep the files uploaded to dockerd slim.
# COPY / /all-contents/

USER 1337

ENTRYPOINT ["/bin/sh", "/entrypoint-nightjar.sh"]
