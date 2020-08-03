
"""
Interface for calling out to the discovery map extension point executable.
"""

from typing import Dict, Sequence, Any
import os
import subprocess
from .cached_document import CachedDocument
from .run_cmd import run_with_backoff
from ..validation import validate_discovery_map


class DiscoveryMapRunner:
    """Executes the discovery map extension point executable."""
    __slots__ = (
        '_cached',
        '_executable', 'max_retry_count', 'max_retry_wait_seconds',
    )

    def __init__(
            self,
            executable: Sequence[str],
            temp_dir: str,
    ) -> None:
        self._cached = CachedDocument(
            'discovery_map',
            'discovery-map',
            os.path.join(temp_dir, 'mesh-cache.json'),
            os.path.join(temp_dir, 'mesh-fetching.json'),
            os.path.join(temp_dir, 'mesh-pending.json'),
            validate_discovery_map,
            True,
        )
        self._executable = tuple(executable)
        self.max_retry_count = 5
        self.max_retry_wait_seconds = 60.0

    def get_mesh(self) -> Dict[str, Any]:
        """Get the mesh information from the discovery map."""
        return self.run_discovery_map()

    def run_discovery_map_once(self, output_file: str, previous_version: str) -> int:
        """Execute the executable one time."""
        result = subprocess.run(
            [
                *self._executable,
                '--action-file=' + output_file,
                '--previous-document-version=' + previous_version,
                '--api-version=1',
            ],
            check=False,
        )
        return result.returncode

    def run_discovery_map(self) -> Dict[str, Any]:
        """Execute the discovery map extension point.  Return the raw data structure."""

        def run_it() -> int:
            return self.run_discovery_map_once(self._cached.update_file, self._cached.last_version)

        result = run_with_backoff(run_it, self.max_retry_count, self.max_retry_wait_seconds)
        return self._cached.after_fetch(result)
