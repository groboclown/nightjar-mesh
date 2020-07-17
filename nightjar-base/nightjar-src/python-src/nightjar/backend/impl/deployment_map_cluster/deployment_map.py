
"""
Implementation of the deployment map for the clustering method.
"""

from typing import Iterable, List, Dict, Optional
from . import ecs
from .config import AwsEcsClusterConfig
from ...api.deployment_map import (
    AbcDeploymentMap,
    EnvoyListener,
    EnvoyConfig,
    EnvoyClusterEndpoint,
    EnvoyRoute,
    EnvoyCluster,
    NamedProtectionPort,
)
from ...api.deployment_map.abc_depoyment_map import ServiceDef
from ....protect import RouteProtection, can_use_route, PROTECTION_PRIVATE


class ClusterTaskDeploymentMap(AbcDeploymentMap):
    """
    Loads the tags from tasks inside one or more clusters.  Tasks that
    have matching tags are added to the deployment map.

    There's a bit of an interesting situation here.  The resolution of the deployment
    map is at the EC2 task level, but the service handling the request is one of the
    containers in the task.  In order to help Nightjar understand the deployment
    topology, you must provide task tags.

    In this model, each task running in the clusters that should belong to the
    deployment map must have special tags on the task:

        _ Possibly a required name / value, as defined in the configuration.
            Only tasks that have this name / value will be picked up.
        _ a `NAMESPACE` tag, which is how the deployment map determines the
            namespace each task belongs to.
        _ a `COLOR` tag, which is the color this service belongs to.
        _ a `ROUTE_n` tag, where `n` is some non-negative integer.  This indicates a supported
            URI path that this task handles.
        _ a `WEIGHT_n` tag, where `n` is a matching integer to the route.  If not given, then
            the weight of the route is 1.
        _ a `PORT_n` tag, where `n` is a matching integer to the route.  This is the container
            listening port for the route.  If the route-specific port is not given, the PORT tag
            is tried.  If none are given, a best-effort is made to find a publicized container port.
        _ an optional `PROTOCOL` tag.  Right now, the only supported values are
            "HTTP1.1", and "HTTP2".  It will default to "HTTP1.1" if not given.
        _ an optional SERVICE_NAME tag, which, if not given, then the container name is used instead
            to identify this service.  All services with the same "service name" will
            be grouped into a single "envoy cluster", which means requests for that service
            are sent to any of those tasks.

    If there is just one container in the task, then many things can be assumed, such as the
    service name.  If there is only one container and one published port, then that can also be
    assumed.  Otherwise, the default port and the default service name will be pulled from the
    first container seen, which does not have a guaranteed ordering.
    If multiple containers specify the same container port, then there is no guarantee that the
    host port to container port will be correct.  To help with this, you can also specify the PORT
    tag to be `(container-name):(port)`.
    """
    __slots__ = ('_config', '_task_cache',)

    def __init__(
            self,
            config: AwsEcsClusterConfig,
            initial_namespace_list: Iterable[str],
    ) -> None:
        self._config = config
        ecs.set_aws_config(config)
        self._task_cache: Dict[str, Iterable[ecs.EcsTask]] = {
            namespace: ecs.load_tasks_for_namespace(namespace)
            for namespace in initial_namespace_list
        }

    def load_services_in_namespaces(
            self, namespaces: Iterable[str],
    ) -> Dict[str, Iterable[ServiceDef]]:
        ret: Dict[str, Iterable[ServiceDef]] = {}
        for namespace in namespaces:
            service_defs = [
                ServiceDef(
                    namespace,
                    task.get_service_id(),
                    task.get_service_name(),
                    task.get_color(),
                )
                for task in self._load_namespace_services(namespace, False)
            ]
            ret[namespace] = service_defs
        return ret

    def load_service_config(
            self,
            local_namespace: str,
            service_id_port: NamedProtectionPort,
            external_namespace_protection_ports: Iterable[NamedProtectionPort],
            force_cache_refresh: bool = False,
    ) -> EnvoyConfig:
        """Loads the envoy configuration for use by the given service's envoy sidecar."""
        local_service_id, _, outgoing_mesh_port = service_id_port
        assert local_service_id is not None

        envoy_listeners: List[EnvoyListener] = []
        envoy_clusters: Dict[str, EnvoyCluster] = {}

        # ---------------------------------------------
        # Local Namespace collection

        self._load_namespace_cluster(
            namespace=local_namespace,
            namespace_protection=PROTECTION_PRIVATE,
            namespace_mesh_listening_port=outgoing_mesh_port,
            envoy_clusters=envoy_clusters,
            envoy_listeners=envoy_listeners,
            force_cache_refresh=force_cache_refresh,
        )

        # ---------------------------------------------
        # External Namespace collection

        for port in external_namespace_protection_ports:
            external_namespace, external_namespace_protection, external_port = port
            self._load_namespace_cluster(
                namespace=external_namespace,
                namespace_protection=external_namespace_protection,
                namespace_mesh_listening_port=external_port,
                envoy_clusters=envoy_clusters,
                envoy_listeners=envoy_listeners,
                force_cache_refresh=force_cache_refresh,
            )

        return EnvoyConfig(envoy_listeners, envoy_clusters.values())

    def load_gateway_envoy_configs(
            self, namespaces: Iterable[NamedProtectionPort],
            force_cache_refresh: bool = False,
    ) -> Dict[str, EnvoyConfig]:
        """Loads the gateway config for each namespace, where the gateway is the inbound service
        proxy that directs traffic into the mesh."""
        ret: Dict[str, EnvoyConfig] = {}
        for namespace, namespace_protection, mesh_port in namespaces:
            envoy_listeners: List[EnvoyListener] = []
            envoy_clusters: Dict[str, EnvoyCluster] = {}

            self._load_namespace_cluster(
                namespace=namespace,
                namespace_protection=namespace_protection,
                namespace_mesh_listening_port=mesh_port,
                envoy_clusters=envoy_clusters,
                envoy_listeners=envoy_listeners,
                force_cache_refresh=force_cache_refresh,
            )

            ret[namespace] = EnvoyConfig(envoy_listeners, envoy_clusters.values())

        return ret

    def _load_namespace_cluster(
            self,
            namespace: str,
            namespace_protection: RouteProtection,
            namespace_mesh_listening_port: Optional[int],
            envoy_clusters: Dict[str, EnvoyCluster],
            envoy_listeners: List[EnvoyListener],
            force_cache_refresh: bool,
    ) -> None:
        """
        :param envoy_listeners: The identified listeners, one per task.
        :param envoy_clusters: Identified clusters.  Here, an "envoy cluster" is all
            the instances using the same service name.  Cluster key is the service
            name or the namespace name (for gateway proxies), with a prefix that indicates
            which one we're looking at (to account for a situation where the
            namespace == service name) and which port its listening on (different
            routes can have different ports) and the color.
        """

        # There are 1-n tasks running on an ec2 instance (or Fargate), and each one of
        # those IP addresses is a separate "cluster".

        for task in self._load_namespace_services(namespace, force_cache_refresh):
            routes: Dict[str, Dict[str, int]] = {}

            for route_index in task.get_route_indicies():
                route_path, route_weight, route_protection = task.get_route_weight_protection_for(
                    route_index,
                )
                if (
                        not route_path or
                        not can_use_route([namespace_protection], route_protection)
                ):
                    # route_path being None should not happen, but for safety sake, test for it.
                    # This branch can also happen if the protection level doesn't allow this
                    # route.
                    continue
                container_port, host_port = task.get_route_container_host_port_for(route_index)

                envoy_cluster_name = '{0}-{1}-{2}-{3}'.format(
                    namespace,
                    task.get_service_name(),
                    task.get_color(),
                    container_port,
                )
                if envoy_cluster_name not in envoy_clusters:
                    envoy_clusters[envoy_cluster_name] = EnvoyCluster(
                        envoy_cluster_name,
                        task.get_protocol() == ecs.PROTOCOL__HTTP2,
                        [],
                    )

                # Setup the endpoint in the cluster...
                in_cluster = False
                for endpoint in envoy_clusters[envoy_cluster_name].instances:
                    if endpoint.host == task.host_ip and endpoint.port == host_port:
                        in_cluster = True
                        break
                if not in_cluster:
                    envoy_clusters[envoy_cluster_name].instances.append(
                        EnvoyClusterEndpoint(task.host_ip, host_port)
                    )

                if route_path not in routes:
                    routes[route_path] = {}
                routes[route_path][envoy_cluster_name] = route_weight

            envoy_listeners.append(EnvoyListener(
                namespace_mesh_listening_port,
                [
                    EnvoyRoute(route_path, route_cluster_weights)
                    for route_path, route_cluster_weights in routes.items()
                ],
            ))

    def _load_namespace_services(
            self, namespace: str, force_cache_refresh: bool,
    ) -> Iterable[ecs.EcsTask]:
        if force_cache_refresh or namespace not in self._task_cache:
            self._task_cache[namespace] = tuple(ecs.load_tasks_for_namespace(namespace))
        return self._task_cache[namespace]
