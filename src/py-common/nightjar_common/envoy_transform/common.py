
"""
Common classes for service and gateway transformation, which makes
the construction of the expected data map easier.
"""

from typing import Dict, List, Iterable, Sequence, Literal, Optional, Any
from ..log import debug
from ..validation import validate_proxy_input


class HeaderQueryMatcher:
    """Matches a header value."""
    __slots__ = ('name', 'match_type', 'case_sensitive', 'invert', 'match_value',)

    def __init__(
            self,
            name: str, match_type: str,
            case_sensitive: bool,
            match_value: Optional[str],
            invert: bool = False,
    ) -> None:
        self.name = name
        self.match_type = match_type
        self.case_sensitive = case_sensitive
        self.invert = invert
        self.match_value = match_value or ''

    def get_context(self) -> Dict[str, Any]:
        """Get the return context value."""
        return {
            'name': self.name,
            'match': self.match_value,
            'is_exact_match': self.match_type == 'exact',
            'is_regex_match': self.match_type == 'regex',
            'is_present_match': self.match_type == 'present',
            'is_prefix_match': self.match_type == 'prefix',
            'is_suffix_match': self.match_type == 'suffix',
            'invert_match': self.invert,  # this is ignored for query parameters...
            'case_sensitive': self.case_sensitive,
        }

    def __repr__(self) -> str:
        return repr(self.get_context())

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        if not isinstance(other, HeaderQueryMatcher):
            return False
        return (
            self.name == other.name
            and self.match_type == other.match_type
            and self.case_sensitive == other.case_sensitive
            and self.invert == other.invert
            and self.match_value == other.match_value
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
            hash(self.name)
            + hash(self.match_type)
            + hash(self.case_sensitive)
            + hash(self.invert)
            + hash(self.match_value)
        )


class RoutePathMatcher:
    """Matches the route path."""
    __slots__ = ('path', 'path_type', 'case_sensitive',)

    def __init__(self, path: str, path_type: str, case_sensitive: bool) -> None:
        self.path = path
        self.path_type = path_type
        self.case_sensitive = case_sensitive

    @property
    def is_prefix(self) -> bool:
        """Is the path type a prefix?"""
        return self.path_type == 'prefix'

    @property
    def is_exact(self) -> bool:
        """Is the path type exact?"""
        return self.path_type == 'exact'

    @property
    def is_regex(self) -> bool:
        """Is the path type a regular expression?"""
        return self.path_type == 'regex'

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        if not isinstance(other, RoutePathMatcher):
            return False
        return (
            self.path == other.path
            and self.path_type == other.path_type
            and self.case_sensitive == other.case_sensitive
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
            hash(self.path)
            + hash(self.path_type)
            + hash(self.case_sensitive)
        )


class RouteMatcher:
    """Matches the route path, headers, and query parameters."""
    __slots__ = ('path_matcher', 'header_matchers', 'query_matchers',)

    def __init__(
            self,
            path_matcher: RoutePathMatcher,
            header_matchers: Sequence[HeaderQueryMatcher],
            query_matchers: Sequence[HeaderQueryMatcher],
    ) -> None:
        self.path_matcher = path_matcher
        self.header_matchers = tuple(header_matchers)
        self.query_matchers = tuple(query_matchers)

    def get_context(self) -> Dict[str, Any]:
        """Get the return context base set for this matcher."""
        return {
            'route_path': self.path_matcher.path,
            'path_is_prefix': self.path_matcher.is_prefix,
            'path_is_exact': self.path_matcher.is_exact,
            'path_is_regex': self.path_matcher.is_regex,
            'path_is_case_sensitive': self.path_matcher.case_sensitive,
            'has_header_filters': len(self.header_matchers) > 0,
            'header_filters': [matcher.get_context() for matcher in self.header_matchers],
            'has_query_filters': len(self.query_matchers) > 0,
            'query_filters':  [matcher.get_context() for matcher in self.query_matchers],
        }

    def __repr__(self) -> str:
        return repr(self.get_context())

    # This is used as a dictionary key...
    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        if not isinstance(other, RouteMatcher):
            return False
        return (
            self.path_matcher == other.path_matcher
            # order in the matchers doesn't matter?
            and set(self.header_matchers) == set(other.header_matchers)
            and set(self.query_matchers) == set(other.query_matchers)
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
            hash(self.path_matcher)
            + hash(self.header_matchers)
            + hash(self.query_matchers)
        )


class EnvoyRoute:
    """
    Defines the URL path to cluster matching.
    """
    __slots__ = (
        'matcher', 'cluster_weights',
    )

    def __init__(
            self,
            matcher: RouteMatcher,
            cluster_weights: Dict[str, int],
    ) -> None:
        """
        Create a weighted route.

        The cluster_weight is an association of cluster to the relative weight
        of that cluster routing.  If there are no cluster weights, then this
        route will not be generated.

        "local" routes are for connections between services within the same
        mesh.  Gateway proxies must always set this to False.
        """
        self.matcher = matcher
        self.cluster_weights = dict(cluster_weights)

    @property
    def total_weight(self) -> int:
        """The total cluster weight."""
        return sum(self.cluster_weights.values())

    def is_valid(self) -> bool:
        """Checks if this cluster is valid."""
        for cluster, weight in self.cluster_weights.items():
            if not cluster or weight <= 0:
                return False
        return True

    def get_context(self) -> Optional[Dict[str, Any]]:
        """Get the JSON context data for this route."""
        cluster_count = len(self.cluster_weights)
        if cluster_count <= 0:
            return None

        ret = self.matcher.get_context()
        ret.update({
            'has_one_cluster': cluster_count == 1,
            'has_many_clusters': cluster_count > 1,
            'total_cluster_weight': self.total_weight,
            'clusters': [{
                'cluster_name': cn,
                'route_weight': cw,
            } for cn, cw in self.cluster_weights.items()],
        })
        return ret


class EnvoyListener:
    """
    Defines a port listener in envoy, which corresponds to a namespace.
    """
    __slots__ = ('port', 'routes',)

    def __init__(self, port: Optional[int], routes: Iterable[EnvoyRoute]) -> None:
        self.port = port
        self.routes = list(routes)

    def is_valid(self) -> bool:
        """Checks if this cluster is valid."""
        if self.port is not None:
            return 0 < self.port <= 65535
        return True

    def get_route_contexts(self) -> List[Dict[str, Any]]:
        """Get each route's JSON context data."""
        ret: List[Dict[str, Any]] = []
        for route in self.routes:
            ctx = route.get_context()
            if ctx:
                ret.append(ctx)
        return ret

    def get_context(self) -> Dict[str, Any]:
        """Get the JSON context for this listener, including its routes."""
        return {
            'has_mesh_port': self.port is not None,
            'mesh_port': self.port,
            'routes': self.get_route_contexts(),
        }


HostFormat = Literal['ipv4', 'ipv6', 'hostname']


class EnvoyClusterEndpoint:
    """
    An endpoint within an envoy cluster.
    """
    __slots__ = ('host', 'port', 'host_format',)

    def __init__(self, host: str, port: int, host_format: HostFormat) -> None:
        self.host = host
        self.port = port
        self.host_format = host_format

    def is_valid(self) -> bool:
        """Checks whether the configuration is valid."""
        # Right now, only ipv4 is supported in the proxy input schema.
        return self.host_format == 'ipv4' and 0 < self.port <= 65535

    def get_context(self) -> Dict[str, Any]:
        """Create a json context"""
        return {
            'ipv4': self.host,
            'port': self.port,
        }

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EnvoyClusterEndpoint):
            return False
        return (
            self.host == other.host
            and self.port == other.port
            and self.host_format == other.host_format
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        # host format is implicit in this, so don't need to explicitly calculate.
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
            instances: Iterable[EnvoyClusterEndpoint],
    ) -> None:
        self.cluster_name = cluster_name
        self.uses_http2 = uses_http2
        self.instances: List[EnvoyClusterEndpoint] = list(instances)

    def is_valid(self) -> bool:
        """Checks if this cluster is valid."""
        for instance in self.instances:
            if not instance.is_valid():
                return False
        return True

    def endpoint_count(self) -> int:
        """Count the number of endpoints."""
        return len(self.instances)

    def get_context(self) -> Dict[str, Any]:
        """Get the JSON context for this cluster."""
        instances = self.instances
        if not instances:
            # We need something here, otherwise the route will say the cluster doesn't exist.
            debug(
                "No instances known for cluster {c}; creating temporary one.",
                c=self.cluster_name,
            )
        return {
            'name': self.cluster_name,
            'uses_http2': self.uses_http2,
            'endpoints': [
                inst.get_context()
                for inst in instances
            ],
        }


class EnvoyConfig:
    """An entire configuration data schema for use to import into a mustache template."""
    __slots__ = ('listeners', 'clusters',)

    def __init__(
            self,
            listeners: Iterable[EnvoyListener],
            clusters: Iterable[EnvoyCluster],
    ) -> None:
        self.listeners = list(listeners)
        self.clusters = list(clusters)

    def is_valid(self) -> bool:
        """Checks whether this configuration is valid or not."""
        if not self.listeners or not self.clusters:
            return False
        for listener in self.listeners:
            if not listener.is_valid():
                return False
        for cluster in self.clusters:
            if not cluster.is_valid():
                return False
        return True

    def get_context(
            self, network_name: str, service_member: str,
            admin_port: Optional[int],
    ) -> Dict[str, Any]:
        """Get the JSON context for this configuration."""
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


class EnvoyConfigContext:
    """Configuration context for an envoy instance."""
    __slots__ = ('config', 'network_id', 'service', 'admin_port',)

    def __init__(
            self, config: EnvoyConfig, network_id: str,
            service: str, admin_port: Optional[int],
    ) -> None:
        self.config = config
        self.network_id = network_id
        self.service = service
        self.admin_port = admin_port

    def get_context(self) -> Dict[str, Any]:
        """Get the JSON structure for the context.  This is validated to be in the
        correct format."""
        ret = self.config.get_context(
            self.network_id, self.service, self.admin_port,
        )
        ret['version'] = 'v1'
        return validate_proxy_input(ret)


def is_protocol_http2(protocol: Optional[str]) -> bool:
    """Checks whether the protocol is http2."""
    return protocol is not None and protocol.strip().upper() == 'HTTP2'
