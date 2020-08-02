FROM local/nightjar-standalone

# Configure this image to use the local files for the data store.

ENV DATA_STORE_EXEC "python3 -m nightjar_ds_local"
ENV NJ_DSLOCAL_TEMPLATE_FILE "/nightjar/local/templates.json"
ENV NJ_DSLOCAL_CONFIGURATION_FILE "/nightjar/local/configuration.json"

COPY . /nightjar/local/
