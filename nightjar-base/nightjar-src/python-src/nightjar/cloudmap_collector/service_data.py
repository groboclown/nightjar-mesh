#!/usr/bin/python3


import re
from typing import List, Dict, Optional, TypeVar, Any

from .fetch_servicediscovery import (
    DiscoveryServiceInstance,
    ATTR_AWS_INSTANCE_IPV4,
    ATTR_AWS_INSTANCE_PORT,
)
from nightjar.msg import fatal, note

T = TypeVar('T')
# ARNs are in the form 'arn:aws:servicediscovery:(region):(account):namespace/(namespace)'
NAMESPACE_ARN_PATTERN = re.compile(r'^arn:aws:servicediscovery:[^:]+:[^:]+:namespace/(.*)$')


class EnvoyRoute:
    """
    Defines the URL path to cluster matching.
    """
    def __init__(self, path_prefix: str, cluster_weights: Dict[str, int], is_local_route: bool) -> None:
        if path_prefix[0] == '?':
            self.is_private = True
            self.path_prefix = path_prefix[1:]
        else:
            self.is_private = False
            self.path_prefix = path_prefix
        self.cluster_weights = cluster_weights
        self.total_weight = sum(cluster_weights.values())
        self.is_local_route = is_local_route

    def get_context(self) -> Optional[Dict[str, Any]]:
        # skip creation if:
        #  - this is a proxy to a non-local namespace
        #  - this is a private path.
        if not self.is_local_route and self.is_private:
            return None

        cluster_count = len(self.cluster_weights)
        if cluster_count <= 0:
            return None

        return {
            'route_path': self.path_prefix,
            'has_one_cluster': cluster_count == 1,
            'has_many_clusters': cluster_count > 1,
            'total_cluster_weight': self.total_weight,
            'clusters': [{
                'cluster_name': cn,
                'route_weight': cw,
            } for cn, cw in self.cluster_weights.items()],
        }


class EnvoyListener:
    """
    Defines a port listener in envoy, which corresponds to a namespace.
    """
    def __init__(self, port: Optional[int], routes: List[EnvoyRoute]) -> None:
        self.port = port
        self.routes = list(routes)

    def get_route_contexts(self) -> List[Dict[str, Any]]:
        ret: List[Dict[str, Any]] = []
        for route in self.routes:
            ctx = route.get_context()
            if ctx:
                ret.append(ctx)
        return ret

    def get_context(self) -> Dict[str, Any]:
        return {
            'has_mesh_port': self.port is not None,
            'mesh_port': self.port,
            'routes': self.get_route_contexts(),

            # TODO make this configurable
            'healthcheck_path': '/ping',
        }


class EnvoyCluster:
    """
    Defines a cluster within envoy.  It's already been weighted according to the path.
    """
    def __init__(
            self,
            cluster_name: str,
            uses_http2: bool,
            instances: List[DiscoveryServiceInstance]
    ) -> None:
        self.cluster_name = cluster_name
        self.uses_http2 = uses_http2
        self.instances = list(instances)

    def endpoint_count(self) -> int:
        return len(self.instances)

    def get_context(self) -> Dict[str, Any]:
        instances = self.instances
        if not instances:
            note("No instances known for cluster {c}; creating temporary one.", c=self.cluster_name)
            instances = [DiscoveryServiceInstance('x', {
                # We need something here, otherwise the route will say the cluster doesn't exist.
                ATTR_AWS_INSTANCE_IPV4: '127.0.0.1',
                ATTR_AWS_INSTANCE_PORT: '99',
            })]
        return {
            'name': self.cluster_name,
            'uses_http2': self.uses_http2,
            'endpoints': [{
                'ipv4': inst.ipv4,
                'port': inst.port_str,
            } for inst in instances],
        }


class EnvoyConfig:
    def __init__(
            self,
            listeners: List[EnvoyListener], clusters: List[EnvoyCluster],
            network_name: str, service_member: str,
            admin_port: Optional[int]
    ) -> None:
        self.listeners = listeners
        self.clusters = clusters
        self.network_name = network_name
        self.service_member = service_member
        self.admin_port = admin_port

    def get_context(self) -> Dict[str, Any]:
        if not self.listeners:
            fatal('No listeners; cannot be a proxy.')
        cluster_endpoint_count = sum([c.endpoint_count() for c in self.clusters])
        return {
            'network_name': self.network_name,
            'service_member': self.service_member,
            'has_admin_port': self.admin_port is not None,
            'admin_port': self.admin_port,
            'listeners': [lt.get_context() for lt in self.listeners],
            'has_clusters': cluster_endpoint_count > 0,
            'clusters': [c.get_context() for c in self.clusters],
        }
