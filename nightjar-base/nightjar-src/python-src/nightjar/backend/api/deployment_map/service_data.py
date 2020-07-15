
from typing import List, Iterable, Dict, Union, Optional, Any
from ....msg import fatal, note


class EnvoyRoute:
    """
    Defines the URL path to cluster matching.
    """
    __slots__ = ('path_prefix', 'cluster_weights', 'total_weight',)

    def __init__(
            self, path_prefix: str, cluster_weights: Dict[str, int]
    ) -> None:
        """
        Create a weighted route.

        The path_prefix must start with a '/' or '*'.

        The cluster_weight is an association of cluster to the relative weight
        of that cluster routing.  If there are no cluster weights, then this
        route will not be generated.

        "local" routes are for connections between services within the same
        mesh.  Gateway proxies must always set this to False.
        """
        assert path_prefix[0] in '/*'

        self.path_prefix = path_prefix
        self.cluster_weights = cluster_weights
        self.total_weight = sum(cluster_weights.values())

    def get_context(self) -> Optional[Dict[str, Any]]:
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
    __slots__ = ('port', 'routes',)

    def __init__(self, port: Optional[int], routes: Iterable[EnvoyRoute]) -> None:
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
        }


class EnvoyClusterEndpoint:
    """
    An endpoint within an envoy cluster.
    """
    __slots__ = ('host', 'port',)

    def __init__(self, host: str, port: Union[int, str]) -> None:
        self.host = host
        self.port = port

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EnvoyClusterEndpoint):
            return False
        return self.host == other.host and self.port == other.port

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.host) + hash(self.port)


class EnvoyCluster:
    """
    Defines a cluster within envoy.  It's already been weighted according to the path.
    """
    __slots__ = ('cluster_name', 'uses_http2', 'instances',)

    def __init__(
            self,
            cluster_name: str,
            uses_http2: bool,
            instances: Iterable[EnvoyClusterEndpoint]
    ) -> None:
        self.cluster_name = cluster_name
        self.uses_http2 = uses_http2
        self.instances: List[EnvoyClusterEndpoint] = list(instances)

    def endpoint_count(self) -> int:
        return len(self.instances)

    def get_context(self) -> Dict[str, Any]:
        instances = self.instances
        if not instances:
            # We need something here, otherwise the route will say the cluster doesn't exist.
            note("No instances known for cluster {c}; creating temporary one.", c=self.cluster_name)
        return {
            'name': self.cluster_name,
            'uses_http2': self.uses_http2,
            'endpoints': [{
                'ipv4': inst.host,
                'port': str(inst.port),
            } for inst in instances],
        }


class EnvoyConfig:
    __slots__ = ('listeners', 'clusters',)

    def __init__(
            self,
            listeners: Iterable[EnvoyListener],
            clusters: Iterable[EnvoyCluster],
    ) -> None:
        self.listeners = list(listeners)
        self.clusters = list(clusters)

    def get_context(
            self, network_name: str, service_member: str,
            admin_port: Optional[int]
    ) -> Dict[str, Any]:
        if not self.listeners:
            fatal('No listeners; cannot be a proxy.')
        cluster_endpoint_count = sum([c.endpoint_count() for c in self.clusters])
        return {
            'network_name': network_name,
            'service_member': service_member,
            'has_admin_port': admin_port is not None,
            'admin_port': admin_port,
            'listeners': [lt.get_context() for lt in self.listeners],
            'has_clusters': cluster_endpoint_count > 0,
            'clusters': [c.get_context() for c in self.clusters],
        }

    @staticmethod
    def join(configs: Iterable['EnvoyConfig']) -> 'EnvoyConfig':
        clusters: Dict[str, EnvoyCluster] = {}
        listeners: List[EnvoyListener] = []
        for config in configs:
            remapped_cluster_names: Dict[str, str] = {}
            for cluster in config.clusters:
                # TODO The cluster names need to be unique if the endpoints are unique.
                if cluster.cluster_name in clusters:
                    i = 0
                    new_name = cluster.cluster_name + '_' + str(i)
                    while new_name not in clusters:
                        i += 1
                        new_name = cluster.cluster_name + '_' + str(i)
                    remapped_cluster_names[cluster.cluster_name] = new_name
                    clusters[new_name] = EnvoyCluster(new_name, cluster.uses_http2, cluster.instances)
                else:
                    clusters[cluster.cluster_name] = cluster
            for listener in config.listeners:
                new_routes: List[EnvoyRoute] = []
                for route in listener.routes:
                    new_weights: Dict[str, int] = {}
                    for cluster_name, weight in route.cluster_weights.items():
                        if cluster_name in remapped_cluster_names:
                            new_weights[remapped_cluster_names[cluster_name]] = weight
                        else:
                            new_weights[cluster_name] = weight
                    new_routes.append(EnvoyRoute(route.path_prefix, new_weights))
                # TODO if the listener ports overlap, then that's an error.
                listeners.append(EnvoyListener(listener.port, new_routes))
        return EnvoyConfig(listeners, clusters.values())
