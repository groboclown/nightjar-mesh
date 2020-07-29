
"""
Transforms the discovery map returned data into a service-color specific data format.
"""

from typing import Dict, Any, Union, Optional
# from ..log import warning


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
