
"""
Manage the envoy proxy process.
"""

from typing import List, Optional
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
        return self._proc is not None and (self._proc.poll() is None)

    def start_if_not_running(self) -> None:
        """Start envoy if it is not running."""
        if not self.is_alive():
            debug('Starting {cmd}', cmd=self._config.envoy_cmd)
            self._proc = subprocess.Popen(self._cmd_args())

    def _cmd_args(self) -> List[str]:
        """Create the envoy execution arguments."""
        return [
            *self._config.envoy_cmd,
            '--log-level', self._config.envoy_log_level,
            '-c', self._config.envoy_config_file,
            '--base-id', self._config.envoy_base_id,
        ]

    def stop_envoy(self) -> None:
        """Stop the envoy process."""
        if self._proc:
            status = self._proc.poll()
            if status is None:
                self._proc.send_signal(signal.SIGTERM)
                status = self._proc.wait(self._config.envoy_kill_wait_time)
            if status is None:
                # This is really, really hard to simulate.  So we're not covering it.
                warning("Could not terminate envoy with `sigterm`; running kill")  # pragma no cover
                self._proc.kill()  # pragma no cover
            self._proc = None


def create_envoy_handler(config: Config) -> EnvoyProcess:
    """Create the envoy handler class."""
    return EnvoyProcess(config)
