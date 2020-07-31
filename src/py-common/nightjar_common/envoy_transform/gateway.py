
"""
Transforms the discovery map data output into a gateway specific format.
"""

from typing import List, Dict, Set, Tuple, Any, Union, Optional
from .common import (
    EnvoyConfig,
    EnvoyConfigContext,
    EnvoyCluster,
    EnvoyClusterEndpoint,
    EnvoyListener,
    EnvoyRoute,
    RouteMatcher,
    RoutePathMatcher,
    HeaderQueryMatcher,
    get_service_color_instances_host_type,
    get_service_color_instance_host_format,
    is_protocol_http2,
)
from ..log import warning


def create_gateway_proxy_input(
        discovery_map_data: Dict[str, Any],
        namespace: str,
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

    @param listen_port:
    @param admin_port: non-positive means no admin listening port.
    @param discovery_map_data:
    @param namespace:
    @return:
    """

    network_service_color_list = find_namespace_services(discovery_map_data, namespace)
    if network_service_color_list is None:
        # Could be empty, so check for None instead.
        warning("No namespace {namespace} defined in discovery map.", namespace=namespace)
        return 1
    network_id, service_color_list = network_service_color_list

    # Need to find the routes and their corresponding IP addresses.
    # The transformation here is to:
    #   - each service-color is assigned to its own envoy cluster.
    #   - all the host/ports for a service-color are added to the service-color cluster.
    #   - each route path across the service-colors are joined together.
    #     Gateways only direct public traffic into the namespace.

    # First, create all the clusters.  The cluster name will be service-color, which allows
    # for construction of the name independent of the cluster creation.

    clusters = create_clusters(namespace, service_color_list)
    listeners = create_listeners(listen_port, service_color_list)
    return EnvoyConfigContext(
        EnvoyConfig(listeners, clusters),
        network_id,
        'gateway',
        admin_port if admin_port > 0 else None,
    ).get_context()


def create_clusters(namespace: str, service_colors: List[Dict[str, Any]]) -> List[EnvoyCluster]:
    """Create clusters, one per service color."""
    known_cluster_names: Set[str] = set()
    ret: List[EnvoyCluster] = []
    for service_color in service_colors:
        service = service_color['service']
        color = service_color['color']
        cluster_name = get_service_color_cluster_name(service, color)
        if cluster_name in known_cluster_names:
            warning(
                'Found duplicate service-color {service}-{color} in namespace {namespace}.',
                namespace=namespace,
                service=service,
                color=color,
            )
            continue
        known_cluster_names.add(cluster_name)

        ret.append(EnvoyCluster(
            cluster_name=cluster_name,
            uses_http2=is_protocol_http2(service_color.get('protocol')),
            host_type=get_service_color_instances_host_type(service_color['instances']),
            instances=[
                get_service_color_instance(data)
                for data in service_color['instances']
            ],
        ))
    return ret


def create_listeners(
        listen_port: int,
        service_color_list: List[Dict[str, Any]],
) -> List[EnvoyListener]:
    """Create the listeners with their routes.  For the gateway, there is only one
    listener.  All routes are only the public routes."""

    # As a gateway, there is only one listener.

    # Collate all the service-colors by route.
    # Here, the kind of route matching matters.
    services_by_routes = group_service_colors_by_route(service_color_list)

    routes: List[EnvoyRoute] = []
    for route, service_desc_list in services_by_routes.items():
        cluster_weights: Dict[str, int] = {}
        for cluster_name, service_color in service_desc_list:
            cluster_weights[cluster_name] = service_color['weight']
        routes.append(EnvoyRoute(route, cluster_weights))

    return [
        EnvoyListener(
            listen_port,
            routes,
        ),
    ]


def group_service_colors_by_route(
        service_color_list: List[Dict[str, Any]],
) -> Dict[RouteMatcher, List[Tuple[str, Dict[str, Any]]]]:
    """
    Transforms the service-color list into a dictionary that is:
        route match -> List[service-color cluster name, route-data]

    @param service_color_list:
    @return:
    """

    ret: Dict[RouteMatcher, List[Tuple[str, Dict[str, Any]]]] = {}
    for service_color in service_color_list:
        service = service_color['service']
        color = service_color['color']
        for route in service_color['routes']:
            # only use public routes, because this is a gateway.
            if route['default-access'] is not True:
                continue
            route_group_key = get_route_matcher_key(route)
            if route_group_key not in ret:
                ret[route_group_key] = []
            ret[route_group_key].append((get_service_color_cluster_name(service, color), route,))

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


def get_service_color_cluster_name(service: str, color: str) -> str:
    """Creates the internal envoy cluster name from the service and color."""
    return 'c-{0}-{1}'.format(service, color)


def get_service_color_instance(data: Dict[str, Any]) -> EnvoyClusterEndpoint:
    """Create the endpoint for the service-color instance dictionary."""
    port = int(data['port'])
    host_format = get_service_color_instance_host_format(data)
    host = data[host_format]
    return EnvoyClusterEndpoint(host, port, host_format)


def find_namespace_services(
        discovery_map_data: Dict[str, Any],
        namespace: str,
) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
    """Find the service-colors list for the given namespace."""
    for namespace_obj in discovery_map_data['namespaces']:
        if namespace_obj['namespace'] == namespace:
            ret = namespace_obj['service-colors']
            assert isinstance(ret, list)
            return namespace_obj['network-id'], ret
    return None
