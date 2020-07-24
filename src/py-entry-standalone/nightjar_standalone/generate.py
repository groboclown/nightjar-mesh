
"""
Generate the current configuration.
"""

from typing import Dict, Tuple, Iterable
import os
import pystache  # type: ignore
from nightjar_common import log
from nightjar_common.extension_point.data_store import DataStoreRunner
from nightjar_common.extension_point.discovery_map import DiscoveryMapRunner
from .config import Config, DEFAULT_NAMESPACE, DEFAULT_SERVICE, DEFAULT_COLOR


class Generator:
    """The generic generator class."""
    def generate_file(self) -> int:
        """Runs the generation process.  Returns 0 on no error."""
        raise NotImplementedError()


def create_generator(config: Config) -> Generator:
    """Create the appropriate generator."""
    if config.is_service_proxy_mode():
        return GenerateServiceConfiguration(config)
    return GenerateGatewayConfiguration(config)


class GenerateGatewayConfiguration(Generator):
    """Manages the gateway configuration generation."""
    __slots__ = ('_config', '_data_store', '_discovery_map',)

    def __init__(self, config: Config) -> None:
        self._config = config
        self._data_store = DataStoreRunner(config.data_store_exec, config.temp_dir)
        self._discovery_map = DiscoveryMapRunner(config.discovery_map_exec, config.temp_dir)
        os.makedirs(config.envoy_config_dir, exist_ok=True)

    def generate_file(self) -> int:
        """Runs the generation process."""
        mapping = self._discovery_map.get_gateway()
        for purpose, template in self.get_templates().items():
            purpose_file = os.path.join(self._config.envoy_config_dir, purpose)
            log.debug("Generating configuration file {purpose_file}", purpose_file=purpose_file)
            with open(purpose_file, 'w') as f:
                f.write(pystache.render(template, mapping))
        return 0

    def get_templates(self) -> Dict[str, str]:
        """Get the right templates for this mode (purpose -> template)."""
        all_templates = self._data_store.fetch_templates()
        default_templates: Dict[str, str] = {}
        namespace_templates: Dict[str, str] = {}
        for gateway_template in all_templates['gateway-templates']:
            if gateway_template['protection'] == 'public':
                namespace = gateway_template['namespace']
                purpose = gateway_template['purpose']
                if namespace == self._config.namespace:
                    namespace_templates[purpose] = gateway_template['template']
                elif namespace == DEFAULT_NAMESPACE:
                    default_templates[purpose] = gateway_template['template']
        return namespace_templates or default_templates


class GenerateServiceConfiguration(Generator):
    """Manages the service configuration generation."""
    __slots__ = ('_config', '_data_store', '_discovery_map',)

    def __init__(self, config: Config) -> None:
        self._config = config
        self._data_store = DataStoreRunner(config.data_store_exec, config.temp_dir)
        self._discovery_map = DiscoveryMapRunner(config.discovery_map_exec, config.temp_dir)
        os.makedirs(config.envoy_config_dir, exist_ok=True)

    def generate_file(self) -> int:
        """Runs the generation process."""
        mapping = self._discovery_map.get_service()
        for purpose, template in self.get_templates().items():
            purpose_file = os.path.join(self._config.envoy_config_dir, purpose)
            log.debug("Generating configuration file {purpose_file}", purpose_file=purpose_file)
            with open(purpose_file, 'w') as f:
                f.write(pystache.render(template, mapping))
        return 0

    def get_templates(self) -> Dict[str, str]:
        """Get the right templates for this mode (purpose -> template)."""
        all_templates = self._data_store.fetch_templates()
        possible_templates: Dict[Tuple[str, str, str], Dict[str, str]] = {}
        for service_template in all_templates['gateway-templates']:
            namespace = service_template['namespace']
            service = service_template['service']
            color = service_template['color']
            if self.is_possible_match(namespace, service, color):
                purpose = service_template['purpose']
                key = (namespace, service, color,)
                if key not in possible_templates:
                    possible_templates[key] = {}
                possible_templates[key][purpose] = service_template['template']
        return possible_templates[self.get_best_match(possible_templates.keys())]

    def is_possible_match(self, namespace: str, service: str, color: str) -> bool:
        """Are the given arguments possible matches?"""
        return (
            namespace in (DEFAULT_NAMESPACE, self._config.namespace)
            and
            service in (DEFAULT_SERVICE, self._config.service)
            and
            color in (DEFAULT_COLOR, self._config.color)
        )

    def get_best_match(self, keys: Iterable[Tuple[str, str, str]]) -> Tuple[str, str, str]:
        """Finds the best match for the keys to this configuration."""
        best = DEFAULT_NAMESPACE, DEFAULT_SERVICE, DEFAULT_COLOR
        best_key = 0
        for key in keys:
            match = self.get_key_match(key)
            if best_key < match:
                best = key
                best_key = match
        return best

    def get_key_match(self, key: Tuple[str, str, str]) -> int:
        """Get the key match number.  Higher is better.  Only works for default or exact match."""
        return (
            (5 if key[0] == self._config.namespace else 0)
            +
            (3 if key[1] == self._config.service else 0)
            +
            (1 if key[2] == self._config.service else 0)
        )
