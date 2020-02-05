FROM envoyproxy/envoy-alpine:v1.13.0

# Expose the default admin port and service port.
EXPOSE 9901 8080

ENV ENVOY_ADMIN_PORT 9901
ENV SERVICE_PORT 8080
ENV SERVICE_MEMBER NOT_SET
ENV SERVICE_CONTAINER_NAME NOT_SET

# Broken into smaller chunks to make file updates create fewer layers.
COPY nightjar/requirements.txt /tmp/requirements.txt
RUN echo "start" \
    && apk upgrade \
    && apk add --update python3 curl \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && mv /etc/envoy/envoy.yaml /etc/envoy/envoy-example.yaml \
    && echo "end"

COPY nightjar/ /nightjar/
COPY entrypoint-nightjar.sh /entrypoint-nightjar.sh

RUN echo "start" \
    && tr -d '\015' < /entrypoint-nightjar.sh > /tmp/entrypoint-nightjar.sh \
    && mv /tmp/entrypoint-nightjar.sh /entrypoint-nightjar.sh \
    && chmod +x /entrypoint-nightjar.sh \
    && echo "end"

USER 1337

ENTRYPOINT ["/entrypoint-nightjar.sh"]
