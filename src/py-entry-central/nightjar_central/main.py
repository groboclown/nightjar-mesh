
"""
Main program.
"""

from typing import Sequence
import os
import time
from nightjar_common.log import warning, debug
from .config import create_configuration
from .generate import create_generator


def main(_args: Sequence[str]) -> int:
    """Main program."""
    config = create_configuration()
    generator = create_generator(config)

    while True:
        if os.path.exists(config.trigger_stop_file):
            warning("Stopping due to existence of stop trigger file.")
            return 0
        debug('Generating new discovery map.')
        res = generator.update_discovery_map()
        if res != 0:
            warning("Envoy configuration generator returned {code}", code=res)
            if config.exit_on_generation_failure:
                warning("Stopping due to exit-on-failure.")
                return res
            time.sleep(config.failure_sleep)
        else:
            time.sleep(config.refresh_time)
