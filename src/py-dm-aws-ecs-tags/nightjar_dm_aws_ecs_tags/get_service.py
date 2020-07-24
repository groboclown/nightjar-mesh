
"""
Gets the current configuration for a service egress envoy.
"""

from typing import Dict, Union, Any
from .config import Config


def get_service(config: Config) -> Union[int, Dict[str, Any]]:
    """Front-end call."""
    if config.test_mode:
        return 23

    return {}
