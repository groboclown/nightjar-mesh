
"""
Gets the current configuration for the full mesh.
"""

from typing import Dict, Union, Any
from .config import Config


def get_mesh(config: Config) -> Union[int, Dict[str, Any]]:
    """Front-end call."""
    if config.test_mode:
        return {'mesh': True}

    return {}
