
"""
Abstract definition for discovering the service-mesh mappings of meshes to
services to service/colors.

In this construction a "namespace" refers to the service-mesh identifier.
The "service_id" refers to a unique identifier for a specific
service/color; it is unique across all namespaces.
"""

from typing import Tuple, Iterable, Dict, Optional
from abc import ABC
import datetime
from .service_data import EnvoyConfig
from ....protect import RouteProtection


NamedProtectionPort = Tuple[str, RouteProtection, Optional[int]]


class ServiceDef:
    __slots__ = ('namespace_id', 'service_id', 'group_service_name', 'group_color_name',)

    def __init__(self, namespace_id: str, service_id: str, service: str, color: str) -> None:
        self.namespace_id = namespace_id
        self.service_id = service_id
        self.group_service_name = service
        self.group_color_name = color


class AbcDeploymentMap(ABC):
    def load_service_config(
            self,
            service_id_port: NamedProtectionPort,
            external_namespace_protection_ports: Iterable[NamedProtectionPort],
            force_cache_refresh: bool = False,
    ) -> EnvoyConfig:
        """
        Constructs the Envoy configuration for a service sidecar that directs
        outbound service traffic to the rest of the service-mesh, both internal and
        external.

        The local service's namespace will have the protection-level routes available.
        """
        raise NotImplementedError()

    def load_services_in_namespaces(self, namespace: Iterable[str]) -> Dict[str, Iterable[ServiceDef]]:
        """
        Retrieve all the service IDs and their associated service/color description from the
        given namespaces.  The returned mapping is namespace_id -> associated services.
        """
        raise NotImplementedError()

    def load_gateway_envoy_configs(
            self,
            namespaces: Iterable[NamedProtectionPort],
            force_cache_refresh: bool = False,
    ) -> Dict[str, EnvoyConfig]:
        """
        Loads the envoy configuration for a gateway service-mesh, directing
        inbound traffic to the services within the service-mesh.

        The returned list of configurations should be able to have their
        listeners and clusters joined together, if necessary.
        """
        raise NotImplementedError()


def skip_reload(
        cache_load_time: Optional[datetime.datetime], refresh_cache: bool, cache_expiration: datetime.timedelta
) -> bool:
    if not cache_load_time or refresh_cache:
        return False
    return datetime.datetime.now() - cache_load_time < cache_expiration
