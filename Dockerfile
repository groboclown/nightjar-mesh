FROM busybox
LABEL author=https://github.com/groboclown/nightjar-mesh

# This may need to switch to alpine so we can grab the certificates easier.
# It'll still be small, but not as small.
# FROM alpine:3.4
# RUN apk add --no-cache ca-certificates apache2-utils


# Declare a volume, so that the examples can be shared by other containers.
VOLUME ["/shared"]

COPY dist/nightjar-mesh /nightjar-mesh
COPY bin/entrypoint-nightjar.sh /entrypoint-nightjar.sh
ADD examples/envoy-proxy /shared/envoy-proxy

# Avoid adding an extra "RUN" layer to the docker script by directly running
# "sh" and pass in the right script.
CMD [ "/bin/sh", "/entrypoint-nightjar.sh" ]
