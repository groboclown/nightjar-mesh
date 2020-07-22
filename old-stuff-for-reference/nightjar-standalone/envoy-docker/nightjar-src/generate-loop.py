#!/usr/bin/python3

"""
Runs the nightjar loop for the stand-alone container.

This is the main executable.  As much configuration as possible is defined through environment
variables.
"""

from typing import Optional, Any
import os
import sys
import subprocess
import signal
import tempfile
import shutil
import pystache

ENVOY_CMD = os.environ.get('ENVOY_EXEC', '/usr/local/bin/envoy')
ENVOY_LOG_LEVEL = os.environ.get('ENVOY_LOG_LEVEL', 'info')
ENVOY_BASE_ID = os.environ.get('ENVOY_BASE_ID', '0')

ENVOY_CONFIGURATION_FILE = os.environ.get('ENVOY_CONFIGURATION_TEMPLATE', 'envoy-config.yaml')
TRIGGER_STOP_FILE = os.environ.get('TRIGGER_STOP_FILE', '/tmp/stop.txt')

DISCOVERY_MAP_EXEC = os.environ.get('DISCOVERY_MAP_EXEC')
DATA_STORE_EXEC = os.environ.get('DATA_STORE_EXEC')


def get_env_pos_int_value(key: str, default_value: int) -> int:
    """Get an environment value as an integer.  If it doesn't convert cleanly to an
    int, or is not given, then the default value is used instead."""
    str_val = os.environ.get(key)
    if str_val:
        try:
            val = int(str_val)
            if val > 0:
                return val
        except ValueError:
            pass
        warning(
            "environment variable `{key}` must be a positive integer; "
            "found `{value}`, using {default_value}",
            key=key,
            value=str_val,
            default_value=default_value,
        )
    return default_value


def get_env_bool_value(key: str, default_value: bool) -> bool:
    """Get an environment value as a boolean.  If it doesn't convert cleanly to an
    int, or is not given, then the default value is used instead."""
    str_val = os.environ.get(key)
    if str_val:
        return str_val.strip().lower() in ('ok', 'yes', 'true', '1', 'active', 'on',)
    return default_value


REFRESH_TIME = get_env_pos_int_value('REFRESH_TIME', 30)
FAILURE_SLEEP = get_env_pos_int_value('FAILURE_SLEEP', 300)
EXIT_ON_GENERATION_FAILURE = get_env_bool_value('EXIT_ON_GENERATION_FAILURE', False)


def run_discovery_map_once(dest_file: str) -> int:
    """The most basic invocation of the discovery map."""
    result = subprocess.run(
        [
            DISCOVERY_MAP_EXEC,
            '--output-file=' + dest_file,
            '--mode=service',
            '--api-version=1',
        ],
    )
    return result.returncode


def run_discovery_map(dest_file: str) -> None:
    """Run the discovery map, with a possible retry if there was a recoverable error."""
    pass


def run_data_store_once(dest_file: str, previous_version: str) -> int:
    """The most basic invocation of the data store."""
    result = subprocess.run(
        [
            DATA_STORE_EXEC,
            '--activity=template',
            '--action=fetch',
            '--previous-document-version=' + previous_version,
            '--action-file=' + dest_file,
            '--api-version=1',
        ],
    )
    return result.returncode


def run_data_store(dest_file: str, previous_version: str, previous_version_file: str) -> bool:
    pass


def generate_config_files(
        dest_dir: str, previous_template_version: str,
        previous_template_version_file: str,
) -> None:
    """Run the process to generate the configuration files into the output directory."""
    pass


def update_config_files(config_dir: str) -> bool:
    """Updates configuration files.  Returns False if there was an error generating the
    configuration files."""
    tmp_dir = tempfile.mkdtemp()
    try:
        generate_config_files(tmp_dir)

    finally:
        shutil.rmtree(tmp_dir)


class EnvoyProcess:
    """Manages the envoy process"""
    __slots__ = ('_proc', '_config_dir')

    def __init__(self, config_dir: str) -> None:
        self._proc: Optional[subprocess.Popen] = None
        self._config_dir = config_dir

    def is_alive(self) -> bool:
        """Is the envoy process alive?"""
        return self._proc and (self._proc.poll() is not None)

    def start_if_not_running(self) -> None:
        """Start envoy if it is not running."""
        if not self.is_alive():
            self._proc = subprocess.Popen(
                [
                    ENVOY_CMD,
                    '--log-level', ENVOY_LOG_LEVEL,
                    '-c', os.path.join(self._config_dir, ENVOY_CONFIGURATION_FILE),
                    '--base-id', ENVOY_BASE_ID,
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


def warning(message: str, **kvargs: Any) -> None:
    """Send a warning message to stderr."""
    sys.stderr.write('[WARNING] ' + (message.format(**kvargs)) + '\n')
