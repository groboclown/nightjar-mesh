
"""
Gets the current configuration for a gateway envoy.
"""

from typing import Dict, Union, Any
from .config import Config


def get_gateway(config: Config) -> Union[int, Dict[str, Any]]:
    """Front-end call."""
    if config.test_mode:
        return {'gateway': True}

    return {}
