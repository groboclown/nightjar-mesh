# Data Store Implementation: Local

## Usage

In the Nightjar container, set these environment variables, in addition to the [standard settings](standard-usage.md):

```bash
DATA_STORE_EXEC="python3 -m nightjar_ds_local"
NJ_DSLOCAL_TEMPLATE_FILE=/local/template/file.json
NJ_DSLOCAL_DISCOVERY_MAP_FILE=/local/configuration/file.json
```

Details:

* `NJ_DSLOCAL_FILE_TEMPLATES` - The file to use for the templates.  It contains all the template entries.  The default location is `/usr/share/nightjar/data-store/templates.json`
* `NJ_DSLOCAL_FILE_DISCOVERY_MAP` - The file to use for the configurations.  It contains all the configuration entries.  The default location is `/usr/share/nightjar/data-store/discovery-map.json`

Like all data store extension points, this can be used as a discovery map by adding the extra arguments:

```bash
DISCOVERY_MAP_EXEC: python3 -m nightjar_ds_local --document=discovery-map --action=fetch
```
