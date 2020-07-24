
"""
Configuration settings for the standalone.
"""

from typing import Dict
import os
import tempfile
from nightjar_common import log
from nightjar_common import parse_env
from nightjar_common.extension_point.run_cmd import get_env_executable_cmd


ENV__PROXY_MODE = 'NJ_PROXY_MODE'
SERVICE_PROXY_MODE = 'service'
GATEWAY_PROXY_MODE = 'gateway'
TEST_PROXY_MODE = 'test'
DEFAULT_PROXY_MODE = SERVICE_PROXY_MODE
ALLOWED_PROXY_MODES = (SERVICE_PROXY_MODE, GATEWAY_PROXY_MODE, TEST_PROXY_MODE)

ENV__ENVOY_CMD = 'ENVOY_EXEC'
DEFAULT_ENVOY_CMD = '/usr/local/bin/envoy'
ENV__ENVOY_LOG_LEVEL = 'ENVOY_LOG_LEVEL'
DEFAULT_ENVOY_LOG_LEVEL = 'info'
ENV__ENVOY_BASE_ID = 'ENVOY_BASE_ID'
DEFAULT_ENVOY_BASE_ID = '0'

ENV__ENVOY_CONFIG_FILE = 'ENVOY_CONFIGURATION_TEMPLATE'
DEFAULT_ENVOY_CONFIG_FILE = 'envoy-config.yaml'
ENV__ENVOY_CONFIG_DIR = 'ENVOY_CONFIGURATION_DIR'
DEFAULT_ENVOY_CONFIG_DIR = '/etc/envoy/'
ENV__TRIGGER_STOP_FILE = 'TRIGGER_STOP_FILE'
DEFAULT_TRIGGER_STOP_FILE = '/tmp/stop.txt'
ENV__ENVOY_KILL_WAIT_TIME = 'ENVOY_KILL_WAIT_TIME'
DEFAULT_ENVOY_KILL_WAIT_TIME = 60

ENV__REFRESH_TIME = 'REFRESH_TIME'
DEFAULT_REFRESH_TIME = 30
ENV__FAILURE_SLEEP = 'FAILURE_SLEEP'
DEFAULT_FAILURE_SLEEP = 300
ENV__EXIT_ON_GENERATION_FAILURE = 'EXIT_ON_GENERATION_FAILURE'
DEFAULT_EXIT_ON_GENERATION_FAILURE = False
ENV__TEMP_DIR = 'NJ_TEMP_DIR'

ENV__DATA_STORE_EXEC = 'DATA_STORE_EXEC'
ENV__DISCOVERY_MAP_EXEC = 'DISCOVERY_MAP_EXEC'
ENV__NAMESPACE = 'NJ_NAMESPACE'
DEFAULT_NAMESPACE = 'default'
ENV__SERVICE = 'NJ_SERVICE'
DEFAULT_SERVICE = 'default'
ENV__COLOR = 'NJ_COLOR'
DEFAULT_COLOR = 'default'


class Config:  # pylint: disable=R0902
    """Configuration settings"""
    __slots__ = (
        'proxy_mode', 'data_store_exec', 'discovery_map_exec', 'temp_dir',
        'namespace', 'service', 'color',

        'envoy_cmd', 'envoy_log_level', 'envoy_base_id', 'envoy_config_template',
        'envoy_config_dir', 'envoy_config_file', 'envoy_kill_wait_time',

        'trigger_stop_file',
        'refresh_time', 'failure_sleep', 'exit_on_generation_failure',
    )

    def __init__(self, env: Dict[str, str]) -> None:
        self.proxy_mode = env.get(ENV__PROXY_MODE, DEFAULT_PROXY_MODE).lower()
        if self.proxy_mode not in ALLOWED_PROXY_MODES:
            log.warning(
                'Environment variable {key} must be one of {valid}, '
                'but found {value}; using {default} instead.',
                key=ENV__PROXY_MODE,
                value=self.proxy_mode,
                valid=ALLOWED_PROXY_MODES,
                default=DEFAULT_PROXY_MODE,
            )
            self.proxy_mode = DEFAULT_PROXY_MODE
        self.data_store_exec = get_env_executable_cmd(env, ENV__DATA_STORE_EXEC)
        self.discovery_map_exec = get_env_executable_cmd(env, ENV__DISCOVERY_MAP_EXEC)
        self.namespace = env.get(ENV__NAMESPACE, DEFAULT_NAMESPACE)
        self.service = env.get(ENV__SERVICE, DEFAULT_SERVICE)
        self.color = env.get(ENV__COLOR, DEFAULT_COLOR)
        self.envoy_cmd = get_env_executable_cmd(env, ENV__ENVOY_CMD, DEFAULT_ENVOY_CMD)
        self.envoy_log_level = env.get(ENV__ENVOY_LOG_LEVEL, DEFAULT_ENVOY_LOG_LEVEL)
        self.envoy_base_id = env.get(ENV__ENVOY_BASE_ID, DEFAULT_ENVOY_BASE_ID)
        self.envoy_config_template = env.get(ENV__ENVOY_CONFIG_FILE, DEFAULT_ENVOY_CONFIG_FILE)
        self.envoy_config_dir = env.get(ENV__ENVOY_CONFIG_DIR, DEFAULT_ENVOY_CONFIG_DIR)
        self.envoy_config_file = os.path.join(self.envoy_config_dir, self.envoy_config_template)
        self.envoy_kill_wait_time = parse_env.env_as_float(
            env, ENV__ENVOY_KILL_WAIT_TIME, DEFAULT_ENVOY_KILL_WAIT_TIME,
        )
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

    def is_service_proxy_mode(self) -> bool:
        """Is this running in service mode?"""
        return self.proxy_mode == SERVICE_PROXY_MODE

    def is_gateway_proxy_mode(self) -> bool:
        """Is this running in gateway mode?"""
        return self.proxy_mode == GATEWAY_PROXY_MODE


def create_configuration() -> Config:
    """Create and load the configuration."""
    log.EXECUTE_MODEL = 'nightjar-standalone'
    env = dict(os.environ)
    return Config(env)
