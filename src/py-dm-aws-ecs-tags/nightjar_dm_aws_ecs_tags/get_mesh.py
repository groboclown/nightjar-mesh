
"""
Gets the current configuration for the full mesh.
"""

from typing import Dict, List, Tuple, Set, Iterable, Any
from .config import Config
from .ecs import load_mesh_tasks, EcsTask, RouteInfo


def get_mesh(config: Config) -> Dict[str, Any]:
    """Front-end call."""
    if config.test_mode:
        return {'mesh': True}

    sorted_tasks = sort_tasks_by_namespace(load_mesh_tasks(
        config.clusters, config.required_tag_name, config.required_tag_value,
    ))

    return {
        'schema-version': 'v1',
        'document-version': 'none',
        'namespaces': [
            create_namespace_config(namespace, tasks[0], tasks[1])
            for namespace, tasks in sorted_tasks.items()
        ],
    }


def create_namespace_config(
        namespace: str, gateway_tasks: List[EcsTask], service_color_tasks: List[EcsTask],
) -> Dict[str, Any]:
    """Create the discovery-map namespace configuration for the given setup."""
    return {
        'namespace': namespace,
        'network-id': namespace,
        'gateways': create_gateway_config(gateway_tasks),
        'service-colors': create_service_color_configs(service_color_tasks),
    }


def create_gateway_config(gateway_tasks: List[EcsTask]) -> Dict[str, Any]:
    """Create the discovery map for a namespace's gateways."""
    prefer_gateway = False
    protocol = 'HTTP1.1'
    instances: List[Dict[str, Any]] = []
    for task in gateway_tasks:
        protocol_tag = task.get_protocol_tag()
        if protocol_tag:
            # Don't care about the value in this part of the configuration.
            protocol = protocol_tag
        if task.get_prefer_gateway_tag() in ('true', 'yes', '1', 'active', 'on'):
            prefer_gateway = True
        _, host_port = task.get_route_container_host_port_for(-1)
        instances.append({
            'ipv4': task.host_ipv4,
            'port': host_port,
        })
    return {
        'protocol': protocol,
        'prefer-gateway': prefer_gateway,
        'instances': instances,
    }


def create_service_color_configs(service_color_tasks: List[EcsTask]) -> List[Dict[str, Any]]:
    """Create the service color configurations.

    The documentation explicitly declares that service-colors are considered a whole,
    and runtime modification to task tags will produce unexpected behavior.  Because of
    that, we don't need to perform tricky per-task filtering.  Instead, we'll scan the
    tasks in a service-color and use whatever we find first.
    """

    ret: List[Dict[str, Any]] = []
    for service_color, tasks in sort_tasks_by_service_color(service_color_tasks).items():
        service, color = service_color
        for port, routes in get_routes_by_port(tasks).items():
            ret.append({
                'service': service,
                'color': '{0}_{1}'.format(color, port),
                'routes': create_service_color_routes(routes),
                'instances': create_service_color_instances(tasks, port),
                'namespace-egress': create_service_color_namespace_egress(tasks),
            })
    return ret


def create_service_color_routes(routes: List[RouteInfo]) -> List[Dict[str, Any]]:
    """Create the routes for the service-color"""
    ret: List[Dict[str, Any]] = []
    for route in routes:
        if route.is_route_data:
            assert isinstance(route.data, dict)
            ret.append(route.data)
        else:
            assert isinstance(route.data, str)
            # It is either a public or private route, that acts as exact and/or prefix
            if route.data[-1] == '/':
                # Prefix only.
                ret.append({
                    'path-match': {
                        'match-type': 'prefix',
                        'value': route.data,
                    },
                    'weight': route.weight,
                    'namespace-access': [],
                    'default-access': route.is_public_path,
                })
            else:
                # Prefix and exact.  Note ordering.
                ret.append({
                    'path-match': {
                        'match-type': 'exact',
                        'value': route.data,
                    },
                    'weight': route.weight,
                    'namespace-access': [],
                    'default-access': route.is_public_path,
                })
                ret.append({
                    'path-match': {
                        'match-type': 'prefix',
                        'value': route.data + '/',
                    },
                    'weight': route.weight,
                    'namespace-access': [],
                    'default-access': route.is_public_path,
                })
    return ret


def create_service_color_instances(tasks: List[EcsTask], port: int) -> List[Dict[str, Any]]:
    """Create the instances for the service-colors"""
    return [
        {
            'ipv4': task.host_ipv4,
            'port': port,
        }
        for task in tasks
    ]


def create_service_color_namespace_egress(tasks: List[EcsTask]) -> List[Dict[str, Any]]:
    """Create the 'namespace-egress' structure"""
    namespace_ports: Set[Tuple[str, int]] = set()
    for task in tasks:
        namespace_ports.update(set(task.get_namespace_egress_ports()))
    return [
        {
            'namespace': namespace,
            'interfaces': [{'ipv4': '127.0.0.1', 'port': port}],
        }
        for namespace, port in namespace_ports
    ]


def get_routes_by_port(tasks: List[EcsTask]) -> Dict[int, List[RouteInfo]]:
    """Extracts the routes from the first task in the list, and separates
    out the listening ports.  This only looks at the first task, because
    these should all be in the same service-color, so the routes should be
    identical."""

    assert tasks
    task = tasks[0]
    ret: Dict[int, List[RouteInfo]] = {}
    for route_info in task.get_routes():
        if route_info.host_port not in ret:
            ret[route_info.host_port] = []
        ret[route_info.host_port].append(route_info)
    return ret


def sort_tasks_by_service_color(
        service_color_tasks: List[EcsTask]
) -> Dict[Tuple[str, str], List[EcsTask]]:
    """Sort the service-color tasks into service-colors."""
    ret: Dict[Tuple[str, str], List[EcsTask]] = {}
    for task in service_color_tasks:
        service = task.get_service_tag()
        color = task.get_color_tag()
        assert service is not None and color is not None
        service_color = (service, color)
        if service_color not in ret:
            ret[service_color] = []
        ret[service_color].append(task)
    return ret


def sort_tasks_by_namespace(
        tasks: Iterable[EcsTask],
) -> Dict[str, Tuple[List[EcsTask], List[EcsTask]]]:
    """Organize the tasks by their namespace and usage.  Each entry for the
    namespace is a list of gateways, list of service-colors"""
    ret: Dict[str, Tuple[List[EcsTask], List[EcsTask]]] = {}
    for task in tasks:
        namespace = task.get_namespace_tag()
        assert namespace is not None
        if namespace not in ret:
            ret[namespace] = ([], [])
        if task.get_gateway_config():
            ret[namespace][0].append(task)
        elif task.get_service_color_config():
            ret[namespace][1].append(task)
    return ret
