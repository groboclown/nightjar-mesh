# nightjar-mesh in Centralized Mode

**TODO This needs updating.**

Centralized mode for nightjar-mesh uses a backend storage mechanism to keep the configuration information about the envoy proxies.  One container (or some other mechanism) in your environment monitors the Cloud Map setup for changes, and updates the configured envoy files that the nightjar sidecars read.

This uses fewer Cloud Map resources and maintains the envoy templates outside docker images.
