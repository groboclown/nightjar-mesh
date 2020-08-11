
"""
Generate the current configuration.
"""

from typing import Dict, Tuple, Iterable, Optional
import os
import tempfile
import pystache  # type: ignore
from nightjar_common import log
from nightjar_common.extension_point.data_store import DataStoreRunner
from nightjar_common.extension_point.discovery_map import DiscoveryMapRunner
from nightjar_common.envoy_transform.gateway import create_gateway_proxy_input
from nightjar_common.envoy_transform.service import create_service_color_proxy_input
from nightjar_common.extension_point.errors import (
    ExtensionPointRuntimeError, ExtensionPointTooManyRetries,
)
from .config import Config

TEMPLATE_DEFAULT = None


class Generator:
    """The generic generator class."""
    def generate_file(self, listen_port: int, admin_port: int) -> int:
        """Runs the generation process.  Returns 0 on no error."""
        raise NotImplementedError()  # pragma no cover


def create_generator(config: Config) -> Generator:
    """Create the appropriate generator."""
    if config.is_service_proxy_mode():
        return GenerateServiceConfiguration(config)
    if config.is_gateway_proxy_mode():
        return GenerateGatewayConfiguration(config)
    return MockGenerator(config)


class GenerateGatewayConfiguration(Generator):
    """Manages the gateway configuration generation."""
    __slots__ = ('_config', '_data_store', '_discovery_map',)

    def __init__(self, config: Config) -> None:
        self._config = config
        self._data_store = DataStoreRunner(config.data_store_exec, config.temp_dir)
        self._discovery_map = DiscoveryMapRunner(config.discovery_map_exec, config.temp_dir)
        os.makedirs(config.envoy_config_dir, exist_ok=True)

    def generate_file(self, listen_port: int, admin_port: int) -> int:
        """Runs the generation process."""
        try:
            log.debug("Fetching discovery map")
            discovery_map = self._discovery_map.get_mesh()
            mapping = create_gateway_proxy_input(
                discovery_map, self._config.namespace,
                listen_port, admin_port,
            )
            if isinstance(mapping, int):
                log.warning("Could not create mapping.")
                return mapping
            for purpose, template in self.get_templates().items():
                log.debug("Rendering template {purpose}", purpose=purpose)
                rendered = pystache.render(template, mapping)
                generate_envoy_file(self._config, purpose, rendered)
            return 0
        except (ExtensionPointRuntimeError, ExtensionPointTooManyRetries) as err:
            print("[nightjar-standalone] File construction generated error: " + repr(err))
            return 1

    def get_templates(self) -> Dict[str, str]:
        """Get the right templates for this mode (purpose -> template)."""
        log.debug("Fetching templates")
        all_templates = self._data_store.fetch_document('templates')
        default_templates: Dict[str, str] = {}
        namespace_templates: Dict[str, str] = {}
        for gateway_template in all_templates['gateway-templates']:
            namespace = gateway_template['namespace']
            purpose = gateway_template['purpose']
            if namespace == self._config.namespace:
                namespace_templates[purpose] = gateway_template['template']
            elif namespace == TEMPLATE_DEFAULT:
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

    def generate_file(self, listen_port: int, admin_port: int) -> int:
        """Runs the generation process."""
        discovery_map = self._discovery_map.get_mesh()
        mapping = create_service_color_proxy_input(
            discovery_map, self._config.namespace, self._config.service, self._config.color,
            listen_port, admin_port,
        )
        if isinstance(mapping, int):
            log.warning("Could not generate mapping.")
            return mapping
        for purpose, template in self.get_templates().items():
            rendered = pystache.render(template, mapping)
            generate_envoy_file(self._config, purpose, rendered)
        return 0

    def get_templates(self) -> Dict[str, str]:
        """Get the right templates for this mode (purpose -> template)."""
        all_templates = self._data_store.fetch_document('templates')
        possible_templates: Dict[
            Tuple[Optional[str], Optional[str], Optional[str]], Dict[str, str],
        ] = {
            # Ensure defaults are always present...
            (TEMPLATE_DEFAULT, TEMPLATE_DEFAULT, TEMPLATE_DEFAULT): {},
        }
        for service_template in all_templates['service-templates']:
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
            namespace in (TEMPLATE_DEFAULT, self._config.namespace)
            and
            service in (TEMPLATE_DEFAULT, self._config.service)
            and
            color in (TEMPLATE_DEFAULT, self._config.color)
        )

    def get_best_match(
            self, keys: Iterable[Tuple[Optional[str], Optional[str], Optional[str]]],
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Finds the best match for the keys to this configuration."""
        best: Tuple[Optional[str], Optional[str], Optional[str]] = (
            TEMPLATE_DEFAULT, TEMPLATE_DEFAULT, TEMPLATE_DEFAULT,
        )
        best_key = 0
        for key in keys:
            match = self.get_key_match(key)
            if best_key < match:
                best = key
                best_key = match
        return best

    def get_key_match(self, key: Tuple[Optional[str], Optional[str], Optional[str]]) -> int:
        """Get the key match number.  Higher is better.  Only works for default or exact match."""
        return (
            (5 if key[0] == self._config.namespace else 0)
            +
            (3 if key[1] == self._config.service else 0)
            +
            (1 if key[2] == self._config.color else 0)
        )


class MockGenerator(Generator):
    """A test-based generator.  It uses static variables, so watch out for cleanup."""
    __slots__ = ('config',)

    RETURN_CODE = 0
    PASSES_BEFORE_EXIT_CREATION = 0

    def __init__(self, config: Config) -> None:
        self.config = config

    def generate_file(self, listen_port: int, admin_port: int) -> int:
        MockGenerator.PASSES_BEFORE_EXIT_CREATION -= 1
        if MockGenerator.PASSES_BEFORE_EXIT_CREATION == 0:
            with open(self.config.trigger_stop_file, 'w') as f:
                f.write('stop')
        return MockGenerator.RETURN_CODE


def generate_envoy_file(config: Config, file_name: str, contents: str) -> None:
    """Performs the correct construction of the envoy file.  To properly support
    envoy dynamic configurations, the file must be created in a temporary file, then
    replaced via a *move* operation.  Due to potential issues around move, the source
    file must be in the same directory as the target file (due to cross-file system
    move issues)."""

    # Note: this is a bit memory heavy, with the contents of source and target present
    # at the same time.

    out_dir = config.envoy_config_dir
    target_file = os.path.join(out_dir, file_name)

    # First, check if the file needs to be updated.  That means the contents are different.
    if os.path.isfile(target_file):
        with open(target_file, 'r') as f:
            current_contents = f.read()
            if current_contents == contents:
                log.debug(
                    "Contents of {file_name} are the same; not updating.", file_name=file_name
                )
                return

    gen_fd, gen_filename = tempfile.mkstemp(prefix=file_name, dir=out_dir, text=False)
    os.write(gen_fd, contents.encode('utf-8', errors='replace'))
    os.close(gen_fd)
    os.replace(gen_filename, target_file)
    log.log('INFO', "Generated configuration file {file_name}", file_name=file_name)
    log.debug('. . . . . . . . . . . . . . . . . .')
    log.debug_raw(contents)
    log.debug('. . . . . . . . . . . . . . . . . .')
