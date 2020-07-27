# Standard Usage of Nightjar

Across all the entry points and extension points, these concepts are shared.  All extension point authors must use these.


## Entry Points

Entry points (like standalone and central-configurator) use these environment variables:

* `DISCOVERY_MAP_EXEC` - sets the [Discovery Map](extension-points.md#discovery-maps) extension point executable.  This can be a full execution command, such as `-m my_exension_point "with first argument"`
* `DATA_STORE_EXEC` - sets the [Data Store](extension-points.md#data-store) extension point executable.  This can be a full execution command, such as `python3 -m my_exension_point "an argument"`

Each entry point will have its own additional environment variables.


## Service Sidecar

The Nightjar sidecar container that controls the Envoy proxy configuration uses these environment variables:

* `NJ_NAMESPACE` - the namespace to which the service belongs.  If not given, then `default` is assumed.
* `NJ_SERVICE` - the service name that the container is part of.  For the purpose of the sidecar, this only tells the sidecar how to setup the envoy configuration, and is not necessarily used for service discovery.
* `NJ_COLOR` - the service color that the container is part of.  If not given, then `default` is assumed.  This is for allowing different containers to provide alternate implementations or load characteristics.  For the purpose of the sidecar, this only tells the sidecar how to setup the envoy configuration, and is not necessarily used for service discovery.


## Gateway

The Nightjar gateway container controls the Envoy proxy configuration for ingress into the mesh, and uses these environment variables:

* `NJ_NAMESPACE` - the mesh namespace which this gateway proxies.
