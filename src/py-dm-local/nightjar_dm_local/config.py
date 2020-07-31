
"""
Configuration definition and loading.
"""

from typing import Dict
import os

ENV__DATA_FILE = 'NJ_DMLOCAL_DATA_FILE'
DEFAULT_DATA_FILE = '/usr/share/nightjar/discovery-map.json'


class Config:
    """Local configuration."""
    __slots__ = ('data_file',)

    def __init__(self, env: Dict[str, str]) -> None:
        self.data_file = get_data_file(env)


def create_configuration() -> Config:
    """Create and load the configuration."""
    return Config(dict(os.environ))


def get_data_file(env: Dict[str, str]) -> str:
    """Get the base directory defined in the environment."""
    return env.get(ENV__DATA_FILE, DEFAULT_DATA_FILE)
