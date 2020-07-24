
"""
Test the envoy module.
"""

from typing import List
import unittest
import shutil
import platform
from .. import envoy
from ..config import Config, ENV__ENVOY_CMD, ENV__DISCOVERY_MAP_EXEC, ENV__DATA_STORE_EXEC


class EnvoyProcessTest(unittest.TestCase):
    """Test the EnvoyProcess class."""

    def setUp(self) -> None:
        self._sleep_cmd = (
            # For windows, we could use "timeout", but that fails with
            # a redirection error.
            # Instead, we'll use ping against localhost with the argument meaning # of
            # retries == # of seconds to ping.
            ['ping', '127.0.0.1', '-n'] if platform.system() == 'Windows'
            else ['sleep']
        )
        noop_cmd = 'where' if platform.system() == 'Windows' else 'echo'
        self._config = Config({
            ENV__ENVOY_CMD: noop_cmd,
            ENV__DISCOVERY_MAP_EXEC: noop_cmd,
            ENV__DATA_STORE_EXEC: noop_cmd,
        })

    def tearDown(self) -> None:
        shutil.rmtree(self._config.temp_dir)

    def test_kill(self) -> None:
        """Try to explicitly kill the envoy command."""
        envoy_process = MockEnvoyProcess(self._config)

        # Have the process linger around for enough time to try to kill it.
        envoy_process.cmd_args = [*self._sleep_cmd, '60']
        self.assertFalse(envoy_process.is_alive())
        envoy_process.start_if_not_running()
        self.assertTrue(envoy_process.is_alive())
        envoy_process.stop_envoy()
        self.assertFalse(envoy_process.is_alive())


class MockEnvoyProcess(envoy.EnvoyProcess):
    """Allows for constructing the cmd args explicitly."""
    __slots__ = ('cmd_args',)

    def __init__(self, config: Config) -> None:
        envoy.EnvoyProcess.__init__(self, config)
        self.cmd_args: List[str] = list(config.envoy_cmd)

    def _cmd_args(self) -> List[str]:
        return self.cmd_args
