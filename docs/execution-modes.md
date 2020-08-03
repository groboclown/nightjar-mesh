# Supported Execution Modes

Nightjar can run in several execution modes, each in support of different deployment models.

* [Stand-alone](standalone-deployment-model.md): Envoy and nightjar run as a sidecar container to each service.  Nightjar runs the [discovery map extension point](extension-points.md#discovery-maps) to construct the Envoy configuration.  The service communicates with the mesh through the sidecar envoy proxy.
* [Centralized](centralized-deployment-model.md): A single container performs the details construction of the discovery map through its [extension point](extension-points.md#discovery-maps), then commits the constructed discovery point into the [data-store](extension-points.md#data-store).  The stand-alone nightjar instances use the data store implementation used by the centralized producer as the discovery-map extension point.
