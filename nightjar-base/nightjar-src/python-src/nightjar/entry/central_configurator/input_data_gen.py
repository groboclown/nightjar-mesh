
"""
Constructs an input data format for each of the namespaces and service/color envoy proxies.
"""


from typing import List, Tuple, Iterable

from ...backend.api.deployment_map import AbcDeploymentMap, EnvoyConfig, NamedProtectionPort
from ...protect import RouteProtection


def load_namespace_data(
        deployment_map: AbcDeploymentMap, namespaces: Iterable[str],
        protections: Iterable[RouteProtection],
) -> Iterable[Tuple[str, EnvoyConfig]]:
    """
    Generate the per-namespace (e.g. gateway) configuration data.
    """
    npp_list: List[NamedProtectionPort] = []
    for namespace in namespaces:
        for protection in protections:
            npp_list.append((namespace, protection, None))

    namespace_configs = deployment_map.load_gateway_envoy_configs(npp_list)
    return [nc for nc in namespace_configs.items()]


def load_service_color_data(
        deployment_map: AbcDeploymentMap, namespaces: Iterable[str], protection: RouteProtection,
) -> Iterable[Tuple[str, str, str, str, EnvoyConfig]]:
    """
    Generate the per-service/color configuration data.

    Each item returned contains:
        namespace_id, service_id, service, color, config
    """

    services_by_namespace = deployment_map.load_services_in_namespaces(namespaces)
    for namespace, service_list in services_by_namespace.items():
        for service in service_list:
            yield (
                service.namespace_id,
                service.service_id,
                service.group_service_name,
                service.group_color_name,
                deployment_map.load_service_config(
                    namespace,
                    (service.service_id, protection, None),
                    [], False
                )
            )
