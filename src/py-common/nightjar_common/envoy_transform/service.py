
"""
Transforms the discovery map returned data into a service-color specific data format.
"""

# This module performs many repeated scans of the data structure.
# This could be teased out ahead of time into a common class, rather than
# rerunning the searches.

from typing import Dict, List, Set, Tuple, Callable, Any, Union, Optional
from .common import (
    EnvoyConfigContext,
    EnvoyConfig,
    EnvoyCluster,
    EnvoyClusterEndpoint,
    EnvoyListener,
    EnvoyRoute,
    RouteMatcher,
    RoutePathMatcher,
    HeaderQueryMatcher,
    is_protocol_http2,
    get_service_color_instances_host_type,
)
from ..log import warning


def create_service_color_proxy_input(
        discovery_map_data: Dict[str, Any],
        namespace: str,
        service: str,
        color: str,
        listen_port: int,
        admin_port: int,
) -> Union[Dict[str, Any], int]:
    """
    Create the gateway-specific proxy input formatted data based on the namespace
    and the discovery map data.

    Gateways direct network traffic into the namespace.

    The discovery_map_data must be validated against the schema before calling into this
    function.

    This will return a non-zero integer on failure.

    @param admin_port: non-positive means no admin listening port.
    @param listen_port: positive integer for connecting to other services in this namespace.
    @param discovery_map_data:
    @param namespace:
    @param service:
    @param color:
    @return:
    """

    # Note that the requested service-color here doesn't have an impact on the routes
    # created.  That means requests to routes handled by this service-color can be
    # redirected to another instance, or routed internally.

    # Need to find the routes and their corresponding IP addresses for this namespace.

    # Additionally, each external namespace has its own listener with its own set of
    # routes.  Those must follow the namespace protection levels.
    # If the namespace has a "prefer gateway" flag set, then
    # the listening port will forward to that gateway.  Otherwise, it will create additional
    # routing to each of that namespace's routes that are available from this namespace.

    namespace_obj = find_namespace(namespace, discovery_map_data)
    if not namespace_obj:
        warning(
            "No namespace {namespace} found in discovery map.",
            namespace=namespace,
        )
        return 1

    clusters = create_clusters(namespace, service, color, discovery_map_data)
    if clusters is None:
        warning(
            "No namespace {namespace}, service {service}, color {color} found in discovery map.",
            namespace=namespace,
            service=service,
            color=color,
        )
        return 2

    listeners = create_route_listeners(listen_port, namespace, service, color, discovery_map_data)

    return EnvoyConfigContext(
        EnvoyConfig(listeners, clusters),
        namespace_obj['network-id'],
        '{0}-{1}'.format(service, color),
        admin_port,
    ).get_context()


def create_clusters(
        local_namespace: str, local_service: str, local_color: str,
        discovery_map_data: Dict[str, Any],
) -> Optional[List[EnvoyCluster]]:
    """Create all the clusters for this configuration."""
    local_service_colors = find_namespace_service_colors(local_namespace, discovery_map_data)
    if local_service_colors is None:
        return None
    local_service_color = find_service_color(local_service, local_color, local_service_colors)
    if local_service_color is None:
        return None
    return [
        *create_local_namespace_clusters(local_service_colors),
        *create_nonlocal_namespace_clusters(
            local_namespace, local_service_color, discovery_map_data,
        ),
    ]


def create_local_namespace_clusters(
        service_colors: List[Dict[str, Any]],
) -> List[EnvoyCluster]:
    """Create a cluster for each service color.
    For now, the local service-color will forward to any one of the instances.
    This accommodates the use-case where the service may be loaded and calls back
    to itself should be distributed across the instances.  In some situations,
    the load is not an issue and the network overhead is more of one, in which case this
    strategy is not effective.
    """
    ret: List[EnvoyCluster] = []
    for service_color_obj in service_colors:
        cluster = create_service_color_cluster(
            create_local_cluster_name(service_color_obj['service'], service_color_obj['color']),
            service_color_obj,
        )
        if cluster:
            ret.append(cluster)
    return ret


def create_nonlocal_namespace_clusters(
        local_namespace: str,
        local_service_color_obj: Dict[str, Any],
        discovery_map_data: Dict[str, Any],
) -> List[EnvoyCluster]:
    """Create a cluster for each namespace that uses a gateway, and for each namespace
    that doesn't, create one for each of its accessible service-colors."""
    nonlocal_namespaces_obj = find_nonlocal_namespaces(
        local_namespace, local_service_color_obj, discovery_map_data,
    )
    # We now have a list of all non-local namespaces that are route accessible.
    ret: List[EnvoyCluster] = []
    for namespace_obj in nonlocal_namespaces_obj:
        if (
                namespace_obj['gateways']['prefer-gateway'] is True
                and len(namespace_obj['gateways']['instances']) > 0

        ):
            cluster = create_gateway_cluster(
                create_nonlocal_gateway_cluster_name(namespace_obj['namespace']),
                namespace_obj['gateways'],
            )
            if cluster:
                ret.append(cluster)
        else:
            # If gateways are preferred, but there aren't any, use the services directly.
            for service_color_obj in namespace_obj['service-colors']:
                cluster = create_service_color_cluster(
                    create_nonlocal_service_cluster_name(
                        namespace_obj['namespace'],
                        service_color_obj['service'],
                        service_color_obj['color'],
                    ),
                    service_color_obj,
                )
                if cluster:
                    ret.append(cluster)
    return ret


def create_service_color_cluster(
        cluster_name: str,
        service_color_obj: Dict[str, Any],
) -> Optional[EnvoyCluster]:
    """Create a cluster for the given service-color object."""
    is_http2 = is_protocol_http2(service_color_obj.get('protocol'))
    host_type = get_service_color_instances_host_type(service_color_obj['instances'])
    instances: List[EnvoyClusterEndpoint] = []
    for instance_obj in service_color_obj['instances']:
        instances.append(EnvoyClusterEndpoint(
            instance_obj[host_type],
            int(instance_obj['port']),
            host_type,
        ))
    if instances:
        return EnvoyCluster(
            cluster_name,
            is_http2,
            host_type,
            instances,
        )
    return None


def create_gateway_cluster(
        cluster_name: str,
        gateways_obj: Dict[str, Any],
) -> Optional[EnvoyCluster]:
    """Create a cluster for a non-local gateway."""
    is_http2 = is_protocol_http2(gateways_obj['protocol'])
    host_type = get_service_color_instances_host_type(gateways_obj['instances'])
    instances: List[EnvoyClusterEndpoint] = []
    for instance_obj in gateways_obj['instances']:
        instances.append(EnvoyClusterEndpoint(
            instance_obj[host_type],
            int(instance_obj['port']),
            host_type,
        ))
    if instances:
        return EnvoyCluster(
            cluster_name,
            is_http2,
            host_type,
            instances,
        )
    return None


def create_route_listeners(
        listen_port: int,
        namespace: str,
        service: str,
        color: str,
        discovery_map_data: Dict[str, Any],
) -> List[EnvoyListener]:
    """Create all the route listeners."""
    local_route = create_local_route_listener(listen_port, namespace, discovery_map_data)
    nonlocal_routes = create_nonlocal_route_listeners(namespace, service, color, discovery_map_data)
    return [local_route, *nonlocal_routes]


def create_local_route_listener(
        listen_port: int,
        namespace: str,
        discovery_map_data: Dict[str, Any],
) -> EnvoyListener:
    """Create the route listener for the local namespace services."""
    namespace_obj = find_namespace(namespace, discovery_map_data)
    assert namespace_obj is not None

    # Collate all the service-colors by route.
    # Here, the kind of route matching matters.
    services_by_routes = group_service_colors_by_route(
        namespace_obj['service-colors'],
        None,
        create_local_cluster_name,
    )

    routes: List[EnvoyRoute] = []
    for route, service_desc_list in services_by_routes.items():
        cluster_weights: Dict[str, int] = {}
        for cluster_name, service_color in service_desc_list:
            cluster_weights[cluster_name] = service_color['weight']
        routes.append(EnvoyRoute(route, cluster_weights))

    return EnvoyListener(listen_port, routes)


def create_nonlocal_route_listeners(
        namespace: str,
        service: str,
        color: str,
        discovery_map_data: Dict[str, Any],
) -> List[EnvoyListener]:
    """Create all the non-local namespace route listeners."""
    service_colors_obj = find_namespace_service_colors(namespace, discovery_map_data)
    if not service_colors_obj:
        return []
    local_service_color_obj = find_service_color(
        service, color,
        service_colors_obj,
    )
    if not local_service_color_obj:
        return []
    ret: List[EnvoyListener] = []
    for namespace_obj in find_nonlocal_namespaces(
            namespace, local_service_color_obj, discovery_map_data,
    ):
        egress_instance = get_namespace_egress_instance(
            namespace_obj['namespace'], local_service_color_obj,
        )
        # egress_instance must be non-none, due to the data construction in the
        # find_nonlocal_namespaces function.
        assert egress_instance is not None
        if (
                namespace_obj['gateways']['prefer-gateway'] is True
                and len(namespace_obj['gateways']['instances']) > 0
        ):
            listener = create_remote_gateway_listener(
                create_nonlocal_gateway_cluster_name(namespace_obj['namespace']),
                egress_instance,
            )
            if listener:
                ret.append(listener)
        else:
            # Use the services directly.
            listener = create_remote_namespace_listener(
                namespace,
                egress_instance,
                namespace_obj,
            )
            if listener:
                ret.append(listener)
    return ret


def create_remote_gateway_listener(
        cluster_name: str, listen_instance: Dict[str, Any],
) -> Optional[EnvoyListener]:
    """Create a listener for a remote gateway.
    Remote gateway listeners accept all routes sent to them."""
    return EnvoyListener(
        int(listen_instance['port']),
        [EnvoyRoute(
            RouteMatcher(RoutePathMatcher('/', 'prefix', True), [], []),
            {cluster_name: 1},
        )],
    )


def create_remote_namespace_listener(
        local_namespace: str,
        listen_instance: Dict[str, Any],
        namespace_obj: Dict[str, Any],
) -> Optional[EnvoyListener]:
    """Create a listener for a remote service-color."""
    namespace = namespace_obj['namespace']

    # Collate all the service-colors by route.
    services_by_routes = group_service_colors_by_route(
        namespace_obj['service-colors'],
        local_namespace,
        lambda svc, clr: create_nonlocal_service_cluster_name(namespace, svc, clr),
    )

    routes: List[EnvoyRoute] = []
    for route, service_desc_list in services_by_routes.items():
        cluster_weights: Dict[str, int] = {}
        for cluster_name, service_color in service_desc_list:
            cluster_weights[cluster_name] = service_color['weight']
        routes.append(EnvoyRoute(route, cluster_weights))

    return EnvoyListener(int(listen_instance['port']), routes)


def can_local_namespace_access_remote(
        local_namespace: str,
        remote_namespace_obj: Dict[str, Any],
) -> bool:
    """Can this local namespace access any route on the remote namespace object?  This ignores
    the gateway priority, because if the remote namespace has no accessible routes, then
    the cluster will not be used."""
    for service_color_obj in remote_namespace_obj['service-colors']:
        for route_obj in service_color_obj['routes']:
            if can_local_namespace_access_route(local_namespace, route_obj):
                return True
    return False


def find_namespace_service_colors(
        namespace: str,
        discovery_map_data: Dict[str, Any],
) -> Optional[List[Dict[str, Any]]]:
    """Find the the given namespace structure's list of service-colors."""
    for namespace_obj in discovery_map_data['namespaces']:
        if namespace_obj['namespace'] == namespace:
            ret = namespace_obj['service-colors']
            assert isinstance(ret, list)
            return ret
    return None


def find_service_color(
        service: str, color: str, service_colors: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Find the service-color in the list."""
    for service_color_obj in service_colors:
        if service_color_obj['service'] == service and service_color_obj['color'] == color:
            return service_color_obj
    return None


def find_nonlocal_namespaces(
        local_namespace: str,
        local_service_color: Dict[str, Any],
        discovery_map_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Find all the non-local namespaces accessible by the given
    service-color.  Namespaces which are not accessible due to protected
    routes are not returned."""
    remote_namespaces: Set[str] = set()
    for egress_obj in local_service_color['namespace-egress']:
        # it's possible, but ignored, to have the local namespace
        # in the egress list.
        if egress_obj['namespace'] != local_namespace:
            remote_namespaces.add(egress_obj['namespace'])
    ret: List[Dict[str, Any]] = []
    for namespace_obj in discovery_map_data['namespaces']:
        if namespace_obj['namespace'] in remote_namespaces:
            if can_local_namespace_access_remote(local_namespace, namespace_obj):
                ret.append(namespace_obj)
    return ret


def get_namespace_egress_instance(
        remote_namespace: str, service_color: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Find the instance information for the namespace in the service-color."""
    for egress_obj in service_color['namespace-egress']:
        if egress_obj['namespace'] == remote_namespace:
            ret = egress_obj['interface']
            assert isinstance(ret, dict)
            return ret
    return None


def group_service_colors_by_route(
        service_color_list: List[Dict[str, Any]],
        local_namespace_accessing_remote_route: Optional[str],
        create_cluster_name_callback: Callable[[str, str], str],
) -> Dict[RouteMatcher, List[Tuple[str, Dict[str, Any]]]]:
    """
    Transforms the service-color list into a dictionary that is:
        route match -> List[service-color cluster name, route-data]
    If local_namespace_accessing_remote_route is not None, then
    this is a local namespace reaching out to a remote namespace.
    """

    ret: Dict[RouteMatcher, List[Tuple[str, Dict[str, Any]]]] = {}
    for service_color in service_color_list:
        service = service_color['service']
        color = service_color['color']
        for route in service_color['routes']:
            if (
                    local_namespace_accessing_remote_route
                    and not can_local_namespace_access_route(
                        local_namespace_accessing_remote_route, route,
                    )
            ):
                continue

            route_group_key = get_route_matcher_key(route)
            if route_group_key not in ret:
                ret[route_group_key] = []
            ret[route_group_key].append(
                (create_cluster_name_callback(service, color), route,)
            )

    return ret


def get_route_matcher_key(route_def: Dict[str, Any]) -> RouteMatcher:
    """Create the route grouping key."""

    path_match = route_def['path-match']
    path = RoutePathMatcher(
        path_match['value'],
        path_match['match-type'],
        path_match.get('case-sensitive', True),
    )

    headers: List[HeaderQueryMatcher] = []
    if 'headers' in route_def:
        for header_def in route_def['headers']:
            headers.append(parse_header_query_matcher(header_def, 'header-name', True))

    query_params: List[HeaderQueryMatcher] = []
    if 'query-parameters' in route_def:
        for query_def in route_def['query-parameters']:
            query_params.append(parse_header_query_matcher(query_def, 'parameter-name', False))

    return RouteMatcher(path, headers, query_params)


def parse_header_query_matcher(
        value_def: Dict[str, Any],
        name_key: str,
        allow_ignore: bool,
) -> HeaderQueryMatcher:
    """Return the matcher for this value."""
    return HeaderQueryMatcher(
        name=value_def[name_key],
        match_type=value_def['match-type'],
        case_sensitive=value_def.get('case-sensitive', True),
        match_value=value_def.get('value', None),
        invert=False if not allow_ignore else value_def.get('invert', False),
    )


def can_local_namespace_access_route(
        local_namespace: str,
        route_obj: Dict[str, Any],
) -> bool:
    """Can this local namespace access the given route?"""
    for protection in route_obj['namespace-access']:
        if protection['namespace'] == local_namespace:
            return bool(protection['access'])
    return route_obj['default-access'] is True


def find_namespace(
        namespace: str,
        discovery_map_data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Find the service-colors list for the given namespace."""
    for namespace_obj in discovery_map_data['namespaces']:
        assert isinstance(namespace_obj, dict)
        if namespace_obj['namespace'] == namespace:
            return namespace_obj
    return None


def create_local_cluster_name(service: str, color: str) -> str:
    """Create the local service-color cluster name."""
    return "local-{0}-{1}".format(service, color)


def create_nonlocal_gateway_cluster_name(namespace: str) -> str:
    """Create the cluster name for the non-local namespace that uses a gateway."""
    return "remote-{0}-gateway".format(namespace)


def create_nonlocal_service_cluster_name(namespace: str, service: str, color: str) -> str:
    """Create the cluster name for the non-local namespace, service, color."""
    return "remote-{0}-{1}-{2}".format(namespace, service, color)
