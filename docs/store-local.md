# Data Store Implementation: Local

## Usage

In the Nightjar container that uses this discovery map, set the environment variables, in addition to the [standard settings](standard-usage.md):

```bash
DATA_STORE_EXEC="python3 -m nightjar_ds_local"
NJ_DSLOCAL_TEMPLATE_FILE=/local/template/file.json
NJ_DSLOCAL_CONFIGURATION_FILE=/local/configuration/file.json
```

Details:

* `NJ_DSLOCAL_TEMPLATE_FILE` - The file to use for the templates.  It contains all the template entries.  The default location is `/usr/share/nightjar/data-store/templates.json`
* `NJ_DSLOCAL_CONFIGURATION_FILE` - The file to use for the configurations.  It contains all the configuration entries.  The default location is `/usr/share/nightjar/data-store/configurations.json`
