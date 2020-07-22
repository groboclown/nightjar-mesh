# About

The centralized Nightjar container.

In this model, one Nightjar container polls AWS Cloud Map for a list of known namespace IDs.  Whenever a namespace, service, or instance changes, the central container will regenerate the Envoy xDS configuration and upload that to a data store.  All the other envoy proxies will pull their configuration from that data store.

This model allows for limiting access to Cloud Map from service containers, and for limiting the API calls made against Cloud Map.  The instances will now need read access to the data store, but only to a limited resource subset.

The data store currently supports S3 and DynamoDB.  Other stores could be added, such as SSM Parameters.

In this model, each service can use the default templates, or define its own template directory in the meta-data.

The envoy proxies will only be able to listen on one cluster, so if a service needs to listen to multiple public clusters, then each one must be its own sidecar to the service.  This matches up with the behavior of the standalone implementation, where each must be on their own port.

This has the advantage of making envoy proxy configuration much easier to inspect, because it's available from S3, rather than needing to inspect the contents of the containers.


# Data Locations


