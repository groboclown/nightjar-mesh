
"""
Generate the current configuration.
"""

from typing import cast
import os
import json
from nightjar_common.extension_point.data_store import DataStoreRunner
from nightjar_common.extension_point.discovery_map import DiscoveryMapRunner
from nightjar_common.extension_point.errors import (
    ExtensionPointRuntimeError, ExtensionPointTooManyRetries,
)
from .config import Config


class GenerateData:
    """Generates and commits the discovery-map."""

    def update_discovery_map(self) -> int:
        """Generate the new discovery map, and, if it is different than the old one, commit it."""
        raise NotImplementedError()  # pragma no cover


class GenerateDataImpl(GenerateData):
    """Manages the gateway configuration generation."""
    __slots__ = ('_config', '_data_store', '_discovery_map', '_gen_file', '_old_file',)

    def __init__(self, config: Config) -> None:
        self._config = config
        self._data_store = DataStoreRunner(config.data_store_exec, config.temp_dir)
        self._discovery_map = DiscoveryMapRunner(config.discovery_map_exec, config.temp_dir)
        self._gen_file = os.path.join(self._config.temp_dir, 'generated-discovery-map.json')
        self._old_file = os.path.join(self._config.temp_dir, 'last-discovery-map.json')

    def update_discovery_map(self) -> int:
        """Generate the new discovery map, and, if it is different than the old one, commit it."""
        ret = self.generate_discovery_map()
        if ret != 0:
            return ret
        if self.is_generated_map_different():
            ret = self.commit_discovery_map()
        return ret

    def generate_discovery_map(self) -> int:
        """Runs the generation process."""
        try:
            discovery_map = self._discovery_map.get_mesh()
        except ExtensionPointRuntimeError as err:
            print("[nightjar-central] Failed to create the discovery map: " + repr(err))
            return 1
        with open(self._gen_file, 'w') as f:
            json.dump(discovery_map, f)
        return 0

    def is_generated_map_different(self) -> bool:
        """Check if the generated discovery map is different than the last committed one."""
        if not os.path.isfile(self._gen_file):
            # No generated file, so there's nothing to commit
            return False
        if not os.path.isfile(self._old_file):
            # No old version, so it's definitely new.
            return True
        # Simple comparison.  This requires loading both files into memory.  It
        # shouldn't be a problem for this container.
        with open(self._gen_file, 'r') as f:
            new_contents = json.load(f)
        with open(self._old_file, 'r') as f:
            old_contents = json.load(f)
        return cast(bool, new_contents != old_contents)

    def commit_discovery_map(self) -> int:
        """Push the just-generated discovery map to the data store."""
        if os.path.isfile(self._gen_file):
            with open(self._gen_file, 'r') as f:
                data = json.load(f)

            try:
                self._data_store.commit_document('discovery-map', data)
            except (ExtensionPointRuntimeError, ExtensionPointTooManyRetries) as err:
                print("[nightjar_central] " + str(err))
                return 1

            os.replace(self._gen_file, self._old_file)
        return 0


class MockGenerateData(GenerateData):
    """GenerateData for testing only."""
    __slots__ = ('config',)

    RETURN_CODE = 0
    PASSES_BEFORE_EXIT_CREATION = 0

    def __init__(self, config: Config) -> None:
        self.config = config

    def update_discovery_map(self) -> int:
        MockGenerateData.PASSES_BEFORE_EXIT_CREATION -= 1
        if MockGenerateData.PASSES_BEFORE_EXIT_CREATION == 0:
            with open(self.config.trigger_stop_file, 'w') as f:
                f.write('stop')
        return MockGenerateData.RETURN_CODE


def create_generator(config: Config) -> GenerateData:
    """Create the appropriate generator."""
    if config.test_mode:
        return MockGenerateData(config)
    return GenerateDataImpl(config)
