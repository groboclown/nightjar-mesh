#!/usr/bin/python3


from typing import List, Tuple, Dict, Optional, TypeVar
import os
import datetime
import re
import json

from .fetch_servicediscovery import (
    DiscoveryServiceNamespace,
    DiscoveryServiceColor,
    skip_reload,
)
from .service_data import (
    EnvoyConfig,
    EnvoyRoute,
    EnvoyCluster,
    EnvoyListener,
)
from nightjar.msg import fatal, warn, note

T = TypeVar('T')
# ARNs are in the form 'arn:aws:servicediscovery:(region):(account):namespace/(namespace)'
NAMESPACE_ARN_PATTERN = re.compile(r'^arn:aws:servicediscovery:[^:]+:[^:]+:namespace/(.*)$')

MAX_NAMESPACE_COUNT = 99
SERVICE_MEMBER_GATEWAY = '-gateway-'
DEFAULT_SERVICE_PORT = '8080'


# ---------------------------------------------------------------------------
class LocalServiceSetup:
    service_color: Optional[DiscoveryServiceColor]
    cache_load_time: Optional[datetime.datetime]

    def __init__(
            self,
            service_member: str,
            service_member_port: int,
    ) -> None:
        self.service_member = service_member
        self.service_member_port = service_member_port
        self.service_color = None
        self.cache_load_time = None

    def load_service(self, refresh_cache: bool) -> None:
        if skip_reload(self.cache_load_time, refresh_cache):
            return
        self.service_color = DiscoveryServiceColor.from_single_id(self.service_member)
        self.cache_load_time = datetime.datetime.now()

    @staticmethod
    def from_env() -> Optional['LocalServiceSetup']:
        member = os.environ.get('SERVICE_MEMBER', 'NOT_SET').strip()
        if member == 'NOT_SET':
            fatal(
                'Must set SERVICE_MEMBER environment variable to the AWS Cloud Map (service discovery) service ID.'
            )
        if member.lower() == SERVICE_MEMBER_GATEWAY:
            note("Using 'gateway' mode for the proxy.")
            return None

        port_str = os.environ.get('SERVICE_PORT', DEFAULT_SERVICE_PORT)
        valid_port, member_port = _validate_port(port_str)
        if not valid_port:
            fatal(
                "Invalid port for service member ({port}) in SERVICE_PORT, cannot use proxy.",
                port=port_str
            )
        return LocalServiceSetup(member, member_port)


class EnvSetup:
    def __init__(
            self,
            admin_port: int,
            local_service: Optional[LocalServiceSetup],
            namespaces: Dict[str, int],
    ) -> None:
        self.admin_port = admin_port
        self.local_service = local_service
        self.namespace_ports = dict(namespaces)

    def get_loaded_namespaces(self) -> List[DiscoveryServiceNamespace]:
        """Includes the local service, if given."""
        np = dict(self.namespace_ports)
        if self.local_service:
            self.local_service.load_service(False)
            assert self.local_service.service_color is not None
            np[self.local_service.service_color.namespace_id] = self.local_service.service_member_port
        return DiscoveryServiceNamespace.load_namespaces(dict(self.namespace_ports))

    @staticmethod
    def from_env() -> 'EnvSetup':
        admin_port_str = os.environ.get('ENVOY_ADMIN_PORT', '9901')
        admin_port_valid, admin_port = _validate_port(admin_port_str)
        if not admin_port_valid:
            fatal(
                "Must set ENVOY_ADMIN_PORT to a valid port number; found {port}",
                port=admin_port_str
            )
        local_service = LocalServiceSetup.from_env()
        namespaces: Dict[str, int] = {}
        for ni in range(0, MAX_NAMESPACE_COUNT + 1):
            namespace = os.environ.get('NAMESPACE_{0}'.format(ni), '').strip()
            if namespace:
                namespace_port_str = os.environ.get('NAMESPACE_{0}_PORT'.format(ni), 'NOT SET')
                port_valid, port = _validate_port(namespace_port_str)
                if port_valid:
                    namespaces[namespace] = port
                else:
                    warn(
                        'Namespace {index} ({name}) has invalid port value ({port}); skipping it.',
                        index=ni, name=namespace, port=namespace_port_str,
                    )

        return EnvSetup(admin_port, local_service, namespaces)


# ---------------------------------------------------------------------------
def collate_ports_and_clusters(
        admin_port: int,
        namespaces: List[DiscoveryServiceNamespace], local: Optional[LocalServiceSetup],
        refresh_cache: bool
) -> EnvoyConfig:
    """
    Construct the listener groups, which are per namespace, and the clusters
    referenced by the listeners.

    The local service color group will redirect everything to that service
    to within the local container (as long as the paths reference this color).

    In order to support better envoy cluster traffic management, each
    service/color is its own cluster.
    """
    output_listeners: List[EnvoyListener] = []
    output_clusters: List[EnvoyCluster] = []
    is_local_route = False
    service_member: Optional[str] = None
    network_name: Optional[str] = os.environ.get('NETWORK_NAME', None)

    if local:
        is_local_route = True
        local.load_service(refresh_cache)
        if local.service_color:
            service_member = '{0}-{1}'.format(
                local.service_color.group_service_name,
                local.service_color.group_color_name,
            )
            in_namespaces = False
            for namespace in namespaces:
                if namespace.namespace_id == local.service_color.namespace_id:
                    in_namespaces = True
                    network_name = network_name or namespace.namespace_id
                    break
            if not in_namespaces:
                namespaces.extend(DiscoveryServiceNamespace.load_namespaces({
                    local.service_color.namespace_id: local.service_member_port
                }))

    for namespace in namespaces:
        routes: Dict[str, Dict[str, int]] = {}
        namespace.load_services(refresh_cache)
        for service_color in namespace.services:
            service_color.load_instances(refresh_cache)
            if (
                    local
                    and (
                        local.service_member == service_color.service_id
                        or local.service_member == service_color.service_arn
                    )
            ):
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
                    output_clusters.append(cluster)
                    for path, weight in service_color.path_weights.items():
                        if path not in routes:
                            routes[path] = {}
                        routes[path][cluster.cluster_name] = weight
        envoy_routes: List[EnvoyRoute] = [
            EnvoyRoute(path, cluster_weights, is_local_route)
            for path, cluster_weights in routes.items()
        ]
        # Even if there are no routes, still add the listener.
        # During initialization, the dependent containers haven't started yet and may
        # require this proxy to be running before they start.
        listener = EnvoyListener(namespace.namespace_port, envoy_routes)
        output_listeners.append(listener)

    return EnvoyConfig(
        output_listeners, output_clusters,
        network_name or service_member or 'gateway',
        service_member or 'gateway',
        admin_port
    )


# ---------------------------------------------------------------------------


def _validate_port(port_str: str) -> Tuple[bool, int]:
    try:
        port = int(port_str)
    except ValueError:
        port = -1
    return 0 < port < 65536, port


# ---------------------------------------------------------------------------
def create_envoy_config() -> EnvoyConfig:
    env = EnvSetup.from_env()
    namespaces = env.get_loaded_namespaces()
    envoy_config = collate_ports_and_clusters(
        env.admin_port, namespaces, env.local_service, True
    )
    return envoy_config


if __name__ == '__main__':
    print(json.dumps(create_envoy_config().get_context()))
