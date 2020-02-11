#!/usr/bin/python3

"""
Constructs an input data format for each of the namespaces and service/color envoy proxies.
"""


from typing import List, Tuple, Dict, Iterable

from .fetch_servicediscovery import (
    DiscoveryServiceNamespace,
)
from .service_data import (
    EnvoyConfig,
    EnvoyRoute,
    EnvoyCluster,
    EnvoyListener,
)
from nightjar.msg import warn


# ---------------------------------------------------------------------------


def load_namespace_data(namespaces: Iterable[DiscoveryServiceNamespace]) -> Iterable[Tuple[str, EnvoyConfig]]:
    """
    Generate the per-namespace (e.g. gateway) configuration data.
    """
    for namespace in namespaces:
        clusters: List[EnvoyCluster] = []
        routes: Dict[str, Dict[str, int]] = {}
        namespace.load_services(False)
        for service_color in namespace.services:
            service_color.load_instances(False)
            if not service_color.instances:
                warn(
                    "Cluster {s}-{c} has no discovered instances",
                    s=service_color.group_service_name,
                    c=service_color.group_color_name
                )
            cluster = EnvoyCluster(
                '{0}-{1}'.format(service_color.group_service_name, service_color.group_color_name),
                service_color.uses_http2,
                service_color.instances
            )
            if service_color.path_weights:
                clusters.append(cluster)
                for path, weight in service_color.path_weights.items():
                    if path not in routes:
                        routes[path] = {}
                    routes[path][cluster.cluster_name] = weight
        envoy_routes: List[EnvoyRoute] = [
            EnvoyRoute(path, cluster_weights, False)
            for path, cluster_weights in routes.items()
        ]
        # Even if there are no routes, still add the listener.
        # During initialization, the dependent containers haven't started yet and may
        # require this proxy to be running before they start.
        listener = EnvoyListener(namespace.namespace_port, envoy_routes)
        yield 'id:' + namespace.namespace_id, EnvoyConfig([listener], clusters, 'gateway', 'gateway', None)


def load_service_color_data(namespaces: Iterable[DiscoveryServiceNamespace]) -> Iterable[Tuple[str, str, EnvoyConfig]]:
    """
    Generate the per-service/color configuration data.
    """
    for namespace in namespaces:
        namespace.load_services(False)
        for local_service_color in namespace.services:
            routes: Dict[str, Dict[str, int]] = {}
            clusters: List[EnvoyCluster] = []

            for service_color in namespace.services:
                service_color.load_instances(False)
                if local_service_color.service_arn == service_color.service_arn:
                    # The local service should never be in the envoy.
                    pass
                else:
                    if not service_color.instances:
                        warn(
                            "Cluster {s}-{c} has no discovered instances",
                            s=service_color.group_service_name,
                            c=service_color.group_color_name
                        )
                    cluster = EnvoyCluster(
                        '{0}-{1}'.format(service_color.group_service_name, service_color.group_color_name),
                        service_color.uses_http2,
                        service_color.instances
                    )
                    if service_color.path_weights:
                        clusters.append(cluster)
                        for path, weight in service_color.path_weights.items():
                            if path not in routes:
                                routes[path] = {}
                            routes[path][cluster.cluster_name] = weight
            envoy_routes: List[EnvoyRoute] = [
                EnvoyRoute(path, cluster_weights, True)
                for path, cluster_weights in routes.items()
            ]
            # Even if there are no routes, still add the listener.
            # During initialization, the dependent containers haven't started yet and may
            # require this proxy to be running before they start.
            if not local_service_color.group_service_name or not local_service_color.group_color_name:
                warn(
                    'Service ID {s} does not define the SERVICE or COLOR attributes.',
                    s=local_service_color.service_id
                )
                continue
            listener = EnvoyListener(namespace.namespace_port, envoy_routes)
            yield (
                local_service_color.group_service_name,
                local_service_color.group_color_name,
                EnvoyConfig(
                    [listener], clusters, namespace.namespace_id, '{0}-{1}'.format(
                        local_service_color.group_service_name,
                        local_service_color.group_color_name,
                    ), None
                )
            )


def main() -> None:
    # FIXME implement
    pass


if __name__ == '__main__':
    main()
