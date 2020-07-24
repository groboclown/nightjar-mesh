# Discovery Map Implementation: Local

## Usage

In the Nightjar container that uses this discovery map, set the environment variables, in addition to the [standard settings](standard-usage.md):

```bash
DISCOVERY_MAP_EXEC="python3 -m nightjar_dm_local"
NJ_DMLOCAL_BASE_DIR=/some/base/dir
```

Details:

* `NJ_DMLOCAL_BASE_DIR` - The base directory the extension point will search for the files.  This defaults to `/usr/share/nightjar/discovery-map`.


## File Layout

Under the base directory, the extension looks for the best file that matches the request.

* `mesh` - for mesh requests, only one file is returned.  It is located under `mesh.json`.
* `gateway` - gateway requests search, in order:
    * `gateway/(namespace).json`
    * `gateway/default.json`
* `service` - service requests search, in order:
    * `service/(namespace)-(service)-(color).json`
    * `service/(namespace)-(service)-default.json`
    * `service/(namespace)-default-(color).json`
    * `service/(namespace)-default-default.json`
    * `service/default-(service)-(color).json`
    * `service/default-(service)-default.json`
    * `service/default-default-(color).json`
    * `service/default-default-default.json`
