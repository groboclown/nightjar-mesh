# Extension Point Definition

Nightjar uses two kinds of extensions with well-defined interfaces: [discovery maps](#discovery-maps) and [data store](#data-store).  Each of these are implemented as stand-alone programs that run within the nightjar container.

## Discovery Maps

Discovery map extension points construct a document that describe the services and gateways within each namespace in the mesh.

Discovery Map extension point executables are defined in the `DISCOVERY_MAP_EXEC` environment variable.

The executable takes these arguments:

* `--action-file=(filename)` The filename that the executable must generate to contain the JSON-formatted results.  See below for details about the format.
* `--previous-document-version=(version id or blank)` Tells the data store to only generate an output if there is a more recent version of the document than the previously returned one.  If the value is blank, then the output is generated.  Some discovery-map implementations ignore this.
* `--api-version=1` Indicates the extension point interface version to use.

For future compatibility, other arguments may be passed in, but must be ignored.

The executable's exit code must be `0` to indicate the file was generated without issue, `31` to indicate an error that might be recoverable if invoked again, `30` to indicate that there are no newer version, and and any other number to indicate an unrecoverable error.

The environment variables used to launch the main nightjar program will be passed to the extension point executable.

If the extension point returns a recoverable error exit code, then the nightjar parent program will begin an exponential back-off retry scheme to call the extension point again.

The discovery map has the arguments setup in such a way that it could be replaced by a data store execution with hard-coded arguments `--document=discovery-map --action=fetch`.  This allows the stand-alone docker container to be used for both a stand-alone execution mode and for a centralized mode.


### Returned Data

The discovery map extension point must generate json-formatted data to the given output file argument the complete mesh topology as specified in the [discovery-map schema](../schema/discovery-map-schema.yaml).  The entry point that calls the discovery map will transform that data into a format appropriate for consumption by the data store template and according to the current instance's role.


## Data Store

Data store extension points manage document stores for various document types.

The data store extension point executables are defined in the `DATA_STORE_EXEC` environment variable.

The executable takes these arguments:

* `--document=(document name)` Uses entries for the corresponding document, which is currently either "discovery-map" or "templates".
* `--previous-document-version=(version id or blank)` Tells the data store to only generate an output if there is a more recent version of the document than the previously returned one.  If the value is blank, then the output is generated.  This is only used for "pull" actions.
* `--action=(commit / fetch)` Fetches entries from the data store, or commits entries to the data store.
* `--action-file=(filename)`  The input (for commit actions) or output (for fetch actions) file.
* `--api-version=1` Indicates the extension point interface version to use.

For future compatibility, other arguments may be passed in, but must be ignored.

The executable's exit code must be `0` to indicate the file was generated without issue, `31` to indicate an error that might be recoverable if invoked again, `30` to indicate that there are no newer version (only valid for `fetch` actions), and and any other number to indicate an unrecoverable error.

The environment variables used to launch the main nightjar program will be passed to the extension point executable.

If the extension point returns a recoverable error exit code, then the nightjar parent program will begin an exponential back-off retry scheme to call the extension point again.

The discovery map returns data in the [Discovery Map Schema](../schema/discovery-map-schema.yaml) format.  This is a consolidated look at all the envoy configurations across the mesh.  At a high level, it is the Service Data for each configuration.

Each document fetched and retrieved must be a JSON document, but the format is up to the document type.  The only requirement is that the JSON document include the top-level field `document-version` set to a string, which is the value usable in the `--previous-document-version` argument.

When committing a document, the `document-version` value is ignored by the data-store implementation, and the implementation will generate a new document version.  The extension point can change or delete the `--action-file=` file. 

### Fetch and Commit Actions

The data store either runs in fetch or commit modes.

#### Atomic Operations

Because there are multiple files per active configuration, these must be written and accessed in an atomic manner.  An envoy proxy configuration must not have some files from one configuration and some from another.

To support this, the data store provides versions of the different "activity" files (these are currently template and generated configurations).  The data store will receive commands to read from an existing version, or write to a not-yet-created version.

The "version" should support redundant services running.  The use case for the centralized Nightjar model allows for redundancy, meaning multiple writes can happen simultaneously.  Because of this, there may be a race condition where multiple "commits" happen at a relatively close time.  Indeed, there may be a situation where the start/commit happens while another process is in the middle of the start/commit phase.  The data store shouldn't block for another to finish, because of partial failure states, where one service starts a process but dies before it can finish it.

The implementation can clean up old versions.  However, care should be taken to allow for services that have started reading a version to finish reading that version, even if a new version was written.  This doesn't need to be a 100% guarantee, but an effort should be taken to allow reasonably new versions to stay around, or, if a new version is written, to keep the older one around to allow the existing reads to finish.

One way to avoid this scenario involves storing the entire version as a single blob.  This makes debugging a little harder, but makes the implementation much easier.


## Other Kinds of Extension Points

Nightjar has explored the idea of having the Envoy proxy configuration file generation be configurable, so that it can work with more than just Envoy.

This would make the complex logic if transforming the discovery-map output into the envoy template input an extension point, and allow for flexibility in creating different template inputs and template types.  However, it would also make the logic around maintaining and signaling the proxy system more complex.  This might become a future extension point if some of the difficulties here are worked out.
