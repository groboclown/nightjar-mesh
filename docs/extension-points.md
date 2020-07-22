# Extension Point Definition

Nightjar uses two kinds of extensions with well-defined interfaces: [discovery maps](#discovery-maps) and [data store](#data-store).  Each of these are implemented as stand-alone programs that run within the nightjar container.

## Discovery Maps

Discovery Map extension point executables are defined in the `DISCOVERY_MAP_EXEC` environment variable.

The executable takes these arguments:

* `--output-file=(filename)` The filename that the executable must generate to contain the JSON-formatted results.  See below for details about the format.
* `--mode=(gateway / mesh / service)` The contents of the output must be filled with content oriented for one of these configurations.  See below for details.
* `--api-version=1` Indicates the extension point interface version to use.

For future compatibility, other arguments may be passed in, but must be ignored.

The executable's exit code must be `0` to indicate the file was generated without issue, `31` to indicate an error that might be recoverable if invoked again, and and any other number to indicate an unrecoverable error.

The environment variables used to launch the main nightjar program will be passed to the extension point executable.

If the extension point returns a recoverable error exit code, then the nightjar parent program will begin an exponential back-off retry scheme to call the extension point again.


### Discovery Map Execution Modes

Depending on the [execution mode](execution-modes.md), the discovery map will be invoked with different `--mode=` arguments.  The discovery map extension must correctly change the output to match the given mode.

#### Service

In `service` mode, the discovery map must generate a configuration for a single service / color / namespace.  The specific values of each of those must be discovered by the extension point itself, using whatever means it can.  This is primarily used by the stand-alone execution mode.  The extension point may require the end-user to define environmental variables to help discover the values.

The container must provide environment variables `SERVICE_NAME`, `NAMESPACE_NAME`, and `COLOR_NAME`.  The extension point generates a JSON-formatted [service data](#service-data) output file.  The extension may require additional information specified in the environment variables, which the container must provide.

#### Gateway

In `gateway` mode, the discovery map must generate a configuration for a single gateway to a namespace.  The specific value must be discovered by the extension point itself.  This is primarily used to create the gateway endpoint in stand-alone execution mode.

The container must provide the environment variable `NAMESPACE_NAME`.  The extension point generates a JSON-formatted [service data](#service-data) output file.  The extension may require additional information specified in the environment variables, which the container must provide.

#### Mesh

In `mesh` mode, the discovery map must generate a complete [service mesh map](#service-mesh-map) for the network.  This includes each gateway and each service.

## Data Store

The data store extension point executables are defined in the `DATA_STORE_EXEC` environment variable.

The executable takes these arguments:

* `--activity=(activity name)` Uses entries for the corresponding activity, which is either "configuration" or "template".
* `--previous-document-version=(version id or blank)` Tells the data store to only generate an output if there is a more recent version of the document than the previously returned one.  If the value is blank, then the output is generated.  This is only used for "pull" actions.
* `--action=(commit / fetch)` Fetches entries from the data store, or commits entries to the data store.
* `--action-file=(filename)`  The input (for commit actions) or output (for fetch actions) file.
* `--api-version=1` Indicates the extension point interface version to use.

For future compatibility, other arguments may be passed in, but must be ignored.

The executable's exit code must be `0` to indicate the file was generated without issue, `31` to indicate an error that might be recoverable if invoked again, `30` to indicate that there are no new versions, and and any other number to indicate an unrecoverable error.

The environment variables used to launch the main nightjar program will be passed to the extension point executable.

If the extension point returns a recoverable error exit code, then the nightjar parent program will begin an exponential back-off retry scheme to call the extension point again.

### Fetch and Commit Actions

The data store either runs in fetch or commit modes.


## Output Schemas

The extension points must output files that conform to the published [JSON schema formats](../schema).

### Service Data

[Service Data Schema](../schema/service-data-schema.yaml)

### Service Mesh Map

[Service Mesh Map Schema](../schema/service-mesh-map-schema.yaml)

The service mesh map is a consolidated look at all the envoy configurations across the mesh.  At a high level, it is the Service Data for each configuration.

### Data Store Data

[Data Store - Commit Configurations](../schema/commit-configuration-data-store-schema.yaml)

[Data Store - Commit Templates](../schema/commit-template-data-store-schema.yaml)

[Data Store - Fetch Configurations](../schema/fetched-configuration-data-store-schema.yaml)

[Data Store - Fetch Templates](../schema/fetched-template-data-store-schema.yaml)
