
"""
Interface for calling out to the discovery map extension point executable.
"""

from typing import Literal, Dict, Sequence, Any
import os
import subprocess
import json
from .run_cmd import run_with_backoff
from .exceptions import ExtensionPointRuntimeError, ExtensionPointTooManyRetries
from ..validation import validate_service_data, validate_service_mesh_map


CommandMode = Literal['gateway', 'mesh', 'service']


class DiscoveryMapRunner:
    """Executes the discovery map extension point executable."""
    __slots__ = (
        '_executable', 'max_retry_count', 'max_retry_wait_seconds', '_tmpdir',
    )

    def __init__(
            self,
            executable: Sequence[str],
            temp_dir: str,
    ) -> None:
        self._executable = tuple(executable)
        self._tmpdir = temp_dir
        self.max_retry_count = 5
        self.max_retry_wait_seconds = 60.0

    def get_gateway(self) -> Dict[str, Any]:
        """Get the gateway information from the discovery map."""
        output_file = os.path.join(self._tmpdir, 'gateway.json')
        data = self.run_discovery_map('gateway', output_file)
        validate_service_data(data)
        return data

    def get_service(self) -> Dict[str, Any]:
        """Get the service information from the discovery map."""
        output_file = os.path.join(self._tmpdir, 'service.json')
        data = self.run_discovery_map('service', output_file)
        validate_service_data(data)
        return data

    def get_mesh(self) -> Dict[str, Any]:
        """Get the mesh information from the discovery map."""
        output_file = os.path.join(self._tmpdir, 'mesh.json')
        data = self.run_discovery_map('mesh', output_file)
        validate_service_mesh_map(data)
        return data

    def run_discovery_map_once(self, mode: CommandMode, output_file: str) -> int:
        """Execute the executable one time."""
        result = subprocess.run(
            [
                *self._executable,
                '--output-file=' + output_file,
                '--mode=' + mode,
                '--api-version=1',
            ],
            check=False,
        )
        return result.returncode

    def run_discovery_map(self, mode: CommandMode, output_file: str) -> Dict[str, Any]:
        """Execute the discovery map extension point.  Return the raw data structure."""

        def run_it() -> int:
            return self.run_discovery_map_once(mode, output_file)

        def should_retry(return_code: int) -> bool:
            return return_code == 31

        result = run_with_backoff(
            run_it, should_retry, self.max_retry_count, self.max_retry_wait_seconds,
        )
        if result == 31:
            raise ExtensionPointTooManyRetries('discovery map', mode)
        if result != 0:
            raise ExtensionPointRuntimeError('discovery map', mode, result)

        # This can raise many exceptions...
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        return data
