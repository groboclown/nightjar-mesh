
"""
Configuration settings for the standalone.
"""

from typing import Dict
import os
import tempfile
from nightjar_common import log
from nightjar_common.extension_point.run_cmd import get_env_executable_cmd


TEST_PROXY_MODE = 'test'

ENV__TRIGGER_STOP_FILE = 'TRIGGER_STOP_FILE'
DEFAULT_TRIGGER_STOP_FILE = '/tmp/stop.txt'
ENV__ENVOY_KILL_WAIT_TIME = 'ENVOY_KILL_WAIT_TIME'
DEFAULT_ENVOY_KILL_WAIT_TIME = 60

ENV__TEMP_DIR = 'NJ_TEMP_DIR'

ENV__DATA_STORE_EXEC = 'DATA_STORE_EXEC'
ENV__DISCOVERY_MAP_EXEC = 'DISCOVERY_MAP_EXEC'


class Config:  # pylint: disable=R0902
    """Configuration settings"""
    __slots__ = (
        'data_store_exec', 'discovery_map_exec', 'temp_dir',
    )

    def __init__(self, env: Dict[str, str]) -> None:
        self.data_store_exec = get_env_executable_cmd(env, ENV__DATA_STORE_EXEC)
        self.discovery_map_exec = get_env_executable_cmd(env, ENV__DISCOVERY_MAP_EXEC)

        env_temp_dir = env.get(ENV__TEMP_DIR)
        if env_temp_dir:
            self.temp_dir = env_temp_dir
            os.makedirs(self.temp_dir, exist_ok=True)
        else:
            self.temp_dir = tempfile.mkdtemp()


def create_configuration() -> Config:
    """Create and load the configuration."""
    log.EXECUTE_MODEL = 'nightjar-template-manager'
    env = dict(os.environ)
    return Config(env)
