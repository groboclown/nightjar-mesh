
"""
Transforms the discovery map returned data into a service-color specific data format.
"""

from typing import Dict, Any, Union, Optional
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
    @param listen_port: positive integer
    @param discovery_map_data:
    @param namespace:
    @param service:
    @param color:
    @return:
    """

    service_color = find_namespace_service(discovery_map_data, namespace, service, color)
    if service_color is None:
        # Could be empty, so check for None instead.
        warning(
            "No namespace {namespace}, service {service}, color {color} defined in discovery map.",
            namespace=namespace,
            service=service,
            color=color,
        )
        return 1

    # Need to find the routes and their corresponding IP addresses.
    # Also need to find the outgoing namespace IP / ports.  The IP doesn't matter
    # for this case, but the port definitely does.
    raise NotImplementedError()


def find_namespace_service(
        discovery_map_data: Dict[str, Any],
        namespace: str,
        service: str,
        color: str,
) -> Optional[Dict[str, Any]]:
    """Find the service-colors list for the given namespace."""
    for namespace_obj in discovery_map_data['namespaces']:
        if namespace_obj['namespace'] == namespace:
            for service_color in namespace_obj['service-colors']:
                assert isinstance(service_color, dict)
                if service_color['service'] == service and service_color['color'] == color:
                    return service_color
    return None

