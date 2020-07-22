# Supported Execution Modes

Nightjar can run in several execution modes, each in support of different deployment models.

* [Centralized](centralized-deployment-model.md): a central service constructs the Envoy configurations, and makes them available for end-point deployments through the [data-store](extension-points.md#data-store).
* [Stand-alone](standalone-deployment-model.md): each Envoy instance has an accompanying Nightjar container, each of which scans for the service [discovery map](extension-points.md#discovery-maps) independently to construct the Envoy configuration.
