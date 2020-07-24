
"""
Main program.
"""

from typing import Sequence
import os
import time
from .config import create_configuration
from .generate import create_generator


def main(_args: Sequence[str]) -> int:
    """Main program."""
    config = create_configuration()
    generator = create_generator(config)

    while True:
        if os.path.exists(config.trigger_stop_file):
            return 0
        res = generator.generate_file()
        if res != 0:
            if config.exit_on_generation_failure:
                return res
            time.sleep(config.failure_sleep)
        else:
            time.sleep(config.refresh_time)
