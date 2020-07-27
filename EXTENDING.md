# Extending Nightjar to Support New Technologies

Nightjar uses two abstraction levels to support the dynamic generation of the Envoy Proxy configuration:

* [Discovery Map](docs/extension-points.md#discovery-maps) - discovers the services that should be connected into the proxy.  This includes the service address (IP or hostname), the TCP/IP listening port, and the REST API URI endpoints supported by the services.
* [Data Store](docs/extension-points.md#data-store) - stores templates and configured data.

The extension points are executable programs, to allow for many different kinds of implementations that match the comfort level of the developers.  They must follow a rigorous but simple set of requirements.

Note that the discovery map and data store are generic enough that, potentially, you could construct a different entry point program that uses a different proxy technology, like NGinX or HAProxy.
