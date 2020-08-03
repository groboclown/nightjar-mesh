
"""
Configuration settings for the standalone.
"""

from typing import Dict
import os
import tempfile
from nightjar_common import log
from nightjar_common import parse_env
from nightjar_common.extension_point.run_cmd import get_env_executable_cmd


ENV__TRIGGER_STOP_FILE = 'TRIGGER_STOP_FILE'
DEFAULT_TRIGGER_STOP_FILE = '/tmp/stop.txt'
ENV__REFRESH_TIME = 'REFRESH_TIME'
DEFAULT_REFRESH_TIME = 30
ENV__FAILURE_SLEEP = 'FAILURE_SLEEP'
DEFAULT_FAILURE_SLEEP = 300
ENV__EXIT_ON_GENERATION_FAILURE = 'EXIT_ON_GENERATION_FAILURE'
DEFAULT_EXIT_ON_GENERATION_FAILURE = False
ENV__TEMP_DIR = 'NJ_TEMP_DIR'

ENV__DATA_STORE_EXEC = 'DATA_STORE_EXEC'
ENV__DISCOVERY_MAP_EXEC = 'DISCOVERY_MAP_EXEC'


class Config:  # pylint: disable=R0902
    """Configuration settings"""
    __slots__ = (
        'data_store_exec', 'discovery_map_exec', 'temp_dir',

        'trigger_stop_file',
        'refresh_time', 'failure_sleep', 'exit_on_generation_failure',

        'test_mode',
    )

    def __init__(self, env: Dict[str, str]) -> None:
        self.data_store_exec = get_env_executable_cmd(env, ENV__DATA_STORE_EXEC)
        self.discovery_map_exec = get_env_executable_cmd(env, ENV__DISCOVERY_MAP_EXEC)
        self.trigger_stop_file = env.get(ENV__TRIGGER_STOP_FILE, DEFAULT_TRIGGER_STOP_FILE)
        self.refresh_time = parse_env.env_as_float(
            env, ENV__REFRESH_TIME, DEFAULT_REFRESH_TIME,
        )
        self.failure_sleep = parse_env.env_as_float(
            env, ENV__FAILURE_SLEEP, DEFAULT_FAILURE_SLEEP,
        )
        self.exit_on_generation_failure = parse_env.env_as_bool(
            env, ENV__EXIT_ON_GENERATION_FAILURE, DEFAULT_EXIT_ON_GENERATION_FAILURE,
        )

        env_temp_dir = env.get(ENV__TEMP_DIR)
        if env_temp_dir:
            self.temp_dir = env_temp_dir
            os.makedirs(self.temp_dir, exist_ok=True)
        else:
            self.temp_dir = tempfile.mkdtemp()

        self.test_mode = env.get('TEST.MODE', 'x') == 'is active'


def create_configuration() -> Config:
    """Create and load the configuration."""
    log.EXECUTE_MODEL = 'nightjar-central'
    env = dict(os.environ)
    return Config(env)
