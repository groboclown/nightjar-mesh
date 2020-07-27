# Discovery Map Implementation: Local

## Usage

In the Nightjar container that uses this discovery map, set the environment variables, in addition to the [standard settings](standard-usage.md):

```bash
DISCOVERY_MAP_EXEC="python3 -m nightjar_dm_local"
NJ_DMLOCAL_DATA_FILE=/some/base/dir
```

Details:

* `NJ_DMLOCAL_DATA_FILE` - The base directory the extension point will search for the files.  This defaults to `/usr/share/nightjar/discovery-map.json`.
