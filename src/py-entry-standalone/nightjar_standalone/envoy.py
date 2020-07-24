
"""
Manage the envoy proxy process.
"""

from typing import Optional
import signal
import subprocess
from nightjar_common.log import debug, warning
from .config import Config


class EnvoyProcess:
    """Manages the envoy process"""
    __slots__ = ('_proc', '_config')

    def __init__(self, config: Config) -> None:
        self._proc: Optional[subprocess.Popen] = None
        self._config = config

    def is_alive(self) -> bool:
        """Is the envoy process alive?"""
        return self._proc is not None and (self._proc.poll() is not None)

    def start_if_not_running(self) -> None:
        """Start envoy if it is not running."""
        if not self.is_alive():
            debug('Starting {cmd}', cmd=self._config.envoy_cmd)
            self._proc = subprocess.Popen(
                [
                    *self._config.envoy_cmd,
                    '--log-level', self._config.envoy_log_level,
                    '-c', self._config.envoy_config_file,
                    '--base-id', self._config.envoy_base_id,
                ],
            )

    def stop_envoy(self) -> None:
        """Stop the envoy process."""
        if self._proc:
            status = self._proc.poll()
            if status is None:
                self._proc.send_signal(signal.SIGTERM)
                status = self._proc.wait(60)
            if status is None:
                warning("Could not terminate envoy with `sigterm`; running kill.")
                self._proc.kill()
            self._proc = None
