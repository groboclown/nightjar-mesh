
"""
Configuration for the local data store.
"""

from typing import Dict
import os


ENV_NAME__LOCAL_TEMPLATE_FILE = 'NJ_DSLOCAL_TEMPLATE_FILE'
DEFAULT__LOCAL_TEMPLATE_FILE = '/usr/share/nightjar/data-store/templates.json'
ENV_NAME__LOCAL_CONFIGURATION_FILE = 'NJ_DSLOCAL_CONFIGURATION_FILE'
DEFAULT__LOCAL_CONFIGURATION_FILE = '/usr/share/nightjar/data-store/configurations.json'


class Config:
    """The configuration."""
    __slots__ = ('local_template_file', 'local_configuration_file')

    def __init__(self, env: Dict[str, str]) -> None:
        self.local_template_file = get_template_file(env)
        self.local_configuration_file = get_configuration_file(env)


def create_configuration() -> Config:
    """Create and populate the configuration."""
    return Config(dict(os.environ))


def get_configuration_file(env: Dict[str, str]) -> str:
    """Get the configuration file defined in the environment."""
    return env.get(
        ENV_NAME__LOCAL_CONFIGURATION_FILE, DEFAULT__LOCAL_CONFIGURATION_FILE,
    )


def get_template_file(env: Dict[str, str]) -> str:
    """Get the template file defined in the environment"""
    return env.get(
        ENV_NAME__LOCAL_TEMPLATE_FILE, DEFAULT__LOCAL_TEMPLATE_FILE,
    )
