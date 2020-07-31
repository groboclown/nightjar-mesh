
"""
Main program.
"""

from typing import Sequence
import os
import time
from nightjar_common.log import warning, debug
from .config import create_configuration
from .generate import create_generator
from .envoy import create_envoy_handler


def main(_args: Sequence[str]) -> int:
    """Main program."""
    config = create_configuration()
    if not config.is_valid():
        warning("Configuration is invalid.  Cannot start.")
        return 1
    generator = create_generator(config)
    envoy = create_envoy_handler(config)

    while True:
        if os.path.exists(config.trigger_stop_file):
            warning("Stopping due to existence of stop trigger file.")
            envoy.stop_envoy()
            return 0
        debug('Generating envoy files.')
        res = generator.generate_file(config.envoy_listen_port, config.envoy_admin_port)
        if os.path.isfile(config.envoy_config_file):
            debug('Starting envoy.')
            envoy.start_if_not_running()
        if res != 0:
            warning("Envoy configuration generator returned {code}", code=res)
            if config.exit_on_generation_failure:
                warning("Stopping due to exit-on-failure.")
                envoy.stop_envoy()
                return res
            time.sleep(config.failure_sleep)
        else:
            time.sleep(config.refresh_time)
