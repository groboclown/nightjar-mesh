
"""
General API for pulling the service deployment.

Deployments must allow for discovery along these lines:

1. service-mesh, recognized by a "namespace_id".  This is the high level split between separate service meshes.
2. service definition, recognized by a "service_id".  Each service/color has its own service definition,
    and the service definition has a parent namespace_id.
3. service instance, recognized by an "instance_id".  Each running container or other program that is in
    the service definition has its own service instance.  Each service instance has a parent
    service_id.

On top of this, the deployment scan must be able to find out:

* IP or hostname, and listening port (just 1) of the service instances.
* the service name and color name of each service_id.
* Listening URI path, and public or private protection, of each service.
* all the service definitions with the same parent namespace_id.
* all the service instances with the same parent service_id.
"""

from .abc_depoyment_map import (
    AbcDeploymentMap,
    NamedProtectionPort,
)

from .service_data import (
    EnvoyConfig,
    EnvoyCluster,
    EnvoyClusterEndpoint,
    EnvoyRoute,
    EnvoyListener,
)
