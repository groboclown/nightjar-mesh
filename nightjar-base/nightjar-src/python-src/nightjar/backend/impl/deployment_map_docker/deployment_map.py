
"""
Deployment map implementation for docker.
"""

from typing import Iterable, Dict

from .discover_services import AbcDiscoverServices
from ...api.deployment_map import (
    AbcDeploymentMap,
    EnvoyConfig,
    NamedProtectionPort,
)
from ...api.deployment_map.abc_depoyment_map import ServiceDef


class DockerDeploymentMap(AbcDeploymentMap):
    """Docker's deployment map implementation."""
    def __init__(self, discovery: AbcDiscoverServices) -> None:
        self.discovery = discovery

    def load_service_config(
            self, local_namespace: str, service_id_port: NamedProtectionPort,
            external_namespace_protection_ports: Iterable[NamedProtectionPort],
            force_cache_refresh: bool = False,
    ) -> EnvoyConfig:
        pass

    def load_services_in_namespaces(
            self, namespaces: Iterable[str],
    ) -> Dict[str, Iterable[ServiceDef]]:
        pass

    def load_gateway_envoy_configs(
            self, namespaces: Iterable[NamedProtectionPort],
            force_cache_refresh: bool = False,
    ) -> Dict[str, EnvoyConfig]:
        pass
