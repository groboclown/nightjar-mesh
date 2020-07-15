#!/usr/bin/python3

from typing import Tuple, Dict, Iterable, Optional, Any, TypeVar
import os
from ...backend.api.deployment_map import EnvoyConfig, NamedProtectionPort, AbcDeploymentMap
from ...backend.impl.deployment_map import get_deployment_map_impl, get_deployment_map_params
from ...msg import fatal, warn, note
from ...protect import PROTECTION_PUBLIC, PROTECTION_PRIVATE

T = TypeVar('T')

MAX_NAMESPACE_COUNT = 99
SERVICE_MEMBER_GATEWAY = '-gateway-'
DEFAULT_SERVICE_PORT = '8080'
DEFAULT_NAMESPACE = 'stand-alone'


# ---------------------------------------------------------------------------


class EnvSetup:
    def __init__(
            self,
            admin_port: int,
            local_service: Optional[NamedProtectionPort],
            local_namespace: Optional[str],
            namespaces: Dict[str, int],
    ) -> None:
        self.admin_port = admin_port
        self.local_service = local_service
        self.local_namespace = local_namespace
        self.namespace_ports = dict(namespaces)

    @staticmethod
    def from_env() -> 'EnvSetup':
        admin_port_str = os.environ.get('ENVOY_ADMIN_PORT', '9901')
        admin_port_valid, admin_port = _validate_port(admin_port_str)
        if not admin_port_valid:
            fatal(
                "Must set ENVOY_ADMIN_PORT to a valid port number; found {port}",
                port=admin_port_str
            )
        member = os.environ.get('SERVICE_MEMBER', 'NOT_SET').strip()
        if member == 'NOT_SET':
            fatal(
                'Must set SERVICE_MEMBER environment variable to the AWS Cloud Map (service discovery) service ID.'
            )
        local_service: Optional[NamedProtectionPort] = None
        local_namespace: Optional[str] = None
        if member.lower() == SERVICE_MEMBER_GATEWAY:
            note("Using 'gateway' mode for the proxy.")
        else:
            port_str = os.environ.get('SERVICE_PORT', DEFAULT_SERVICE_PORT)
            valid_port, member_port = _validate_port(port_str)
            if not valid_port:
                fatal(
                    "Invalid port for service member ({port}) in SERVICE_PORT, cannot use proxy.",
                    port=port_str
                )
            local_service = (member, PROTECTION_PRIVATE, int(port_str))
            local_namespace = os.environ.get('NAMESPACE', DEFAULT_NAMESPACE)

        namespaces: Dict[str, int] = {}
        for ni in range(0, MAX_NAMESPACE_COUNT + 1):
            namespace = os.environ.get('NAMESPACE_{0}'.format(ni), '').strip()
            if namespace:
                namespace_port_str = os.environ.get('NAMESPACE_{0}_PORT'.format(ni), 'NOT SET')
                port_valid, port = _validate_port(namespace_port_str)
                if port_valid:
                    namespaces[namespace] = port
                else:
                    warn(
                        'Namespace {index} ({name}) has invalid port value ({port}); skipping it.',
                        index=ni, name=namespace, port=namespace_port_str,
                    )

        return EnvSetup(admin_port, local_service, local_namespace, namespaces)


class EnvoyConfigContext:
    __slots__ = ('config', 'network', 'service', 'admin_port',)

    def __init__(self, config: EnvoyConfig, network: str, service: str, admin_port: Optional[int]) -> None:
        self.config = config
        self.network = network
        self.service = service
        self.admin_port = admin_port

    def get_context(self) -> Dict[str, Any]:
        return self.config.get_context(
            self.network, self.service, self.admin_port
        )


# ---------------------------------------------------------------------------


def _validate_port(port_str: str) -> Tuple[bool, int]:
    try:
        port = int(port_str)
    except ValueError:
        port = -1
    return 0 < port < 65536, port


# ---------------------------------------------------------------------------


def get_deployment_map(namespace_names: Iterable[str]) -> AbcDeploymentMap:
    deployment_map_params = get_deployment_map_params()
    deployment_map_name = os.environ['DEPLOYMENTMAP'].strip().lower()
    for param in deployment_map_params:
        if deployment_map_name in param.aliases:
            return get_deployment_map_impl(param.name, param.parse_env_values(), namespace_names)
    raise Exception('Unknown DEPLOYMENTMAP: "{0}"'.format(deployment_map_name))


def create_envoy_config_from_env(env: EnvSetup) -> EnvoyConfigContext:
    discovery_map = get_deployment_map(env.namespace_ports.keys())
    if env.local_service and env.local_namespace:
        return EnvoyConfigContext(
            discovery_map.load_service_config(
                env.local_namespace,
                env.local_service,
                [(nsn, PROTECTION_PUBLIC, nsp) for nsn, nsp in env.namespace_ports.items()],
                True
            ),
            env.local_service[0], env.local_service[0], env.admin_port
        )
    configs = discovery_map.load_gateway_envoy_configs(
        [(nsn, PROTECTION_PUBLIC, nsp) for nsn, nsp in env.namespace_ports.items()],
        True
    )
    return EnvoyConfigContext(
        EnvoyConfig.join(configs.values()),
        'gateway', 'gateway', env.admin_port
    )


def get_envoy_config() -> Dict[str, Any]:
    env = EnvSetup.from_env()
    return create_envoy_config_from_env(env).get_context()
