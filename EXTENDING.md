# Extending Nightjar to Support New Technologies

Nightjar uses two abstraction levels to support the dynamic generation of the Envoy Proxy configuration:

* [Deployment Map](#deployment-map) - discovers the services that should be connected into the proxy.  This includes the service address (IP or hostname), the TCP/IP listening port, and the REST API URI endpoints supported by the services.
* [Data Store](#data-store) - stores cached information used by the [centralized Nightjar model](README-centralized.md).


## Deployment Map

Discovers the list of service instances in a namespace, along with their host, listening ports, and URL path weights.

### What Deployment Map Implementations Must Do

* Provide an implementation of the [`AbcDeploymentMap`](nightjar-base/nightjar-src/python-src/nightjar/backend/api/deployment_map/abc_depoyment_map.py) class.
* Add a hook in [deployment_map.py](nightjar-base/nightjar-src/python-src/nightjar/backend/impl/deployment_map.py) to allow command line tools to use the new implementation.
* Only import the dependency libraries (e.g. `boto3`) when the implementation is created.  This helps save memory by not loading code when it isn't needed.

### Paths, Weights, and Service Locations

The deployment map must be able to associate the IP + listening port of each service with a URI path and weight.  The simple approach here is to use "/" as the path and "1" as the weight for all services. 


## Data Store

A repository of the templates and generated files used by the centralized mode.

### What Data Store Implementations Must Do

* Provide an implementation of the [`AbcDataStoreBackend`](nightjar-base/nightjar-src/python-src/nightjar/backend/api/data_store/abc_backend.py) class.
* Add a hook in [data_store.py](nightjar-base/nightjar-src/python-src/nightjar/backend/impl/data_store.py) that allows command line tools to use the new implementation.
* Only import the dependency libraries (e.g. `boto3`) when the implementation is created.  This helps save memory by not loading code when it isn't needed.

### Atomic Operations

Because there are multiple files per active configuration, these must be written and accessed in an atomic manner.  An envoy proxy configuration must not have some files from one configuration and some from another.

To support this, the data store provides versions of the different "activity" files (these are currently template and generated configurations).  The data store will receive commands to read from an existing version, or write to a not-yet-created version.

The "version" should support redundant services running.  The use case for the centralized Nightjar model allows for redundancy, meaning multiple writes can happen simultaneously.  Because of this, there may be a race condition where multiple "commits" happen at a relatively close time.  Indeed, there may be a situation where the start/commit happens while another process is in the middle of the start/commit phase.  The data store shouldn't block for another to finish, because of partial failure states, where one service starts a process but dies before it can finish it.

The implementation can clean up old versions.  However, care should be taken to allow for services that have started reading a version to finish reading that version, even if a new version was written.  This doesn't need to be a 100% guarantee, but an effort should be taken to allow reasonably new versions to stay around, or, if a new version is written, to keep the older one around to allow the existing reads to finish.

One way to avoid this scenario involves storing the entire version as a single blob.  This makes debugging a little harder, but makes the implementation much easier.  Note that the [manager command](nightjar-base/nightjar-src/python-src/nightjar/entry/central_manager) provides mechanisms to extract data to help with debugging.


#### Reading Data from an Existing Version

Reading data involves pulling files ("purposes") from the data store associated with a specific version.
