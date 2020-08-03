
"""
Configuration for the local data store.
"""

from typing import Dict, Optional
import os

ENV_FORMAT__LOCAL_FILE = 'NJ_DSLOCAL_FILE_{0}'
DEFAULT_FORMAT__LOCAL_FILE = '/usr/share/nightjar/data-store/{0}.json'

ENV_NAME__LOCAL_FILE_TEMPLATES = ENV_FORMAT__LOCAL_FILE.format('TEMPLATES')
DEFAULT__LOCAL_FILE_TEMPLATE = DEFAULT_FORMAT__LOCAL_FILE.format('templates')
ENV_NAME__LOCAL_FILE_DISCOVERY_MAP = ENV_FORMAT__LOCAL_FILE.format('DISCOVERY_MAP')
DEFAULT__LOCAL_FILE_DISCOVERY_MAP = DEFAULT_FORMAT__LOCAL_FILE.format('discovery-map')


class Config:
    """The configuration."""
    __slots__ = ('local_files',)

    def __init__(self, env: Dict[str, str]) -> None:
        self.local_files = {
            'templates': get_templates_file(env),
            'discovery-map': get_discovery_map_file(env),
        }

    def get_file(self, document: str) -> Optional[str]:
        """Get the local file for the document.  Returns None if it isn't valid."""
        return self.local_files.get(document)


def create_configuration() -> Config:
    """Create and populate the configuration."""
    return Config(dict(os.environ))


def get_discovery_map_file(env: Dict[str, str]) -> str:
    """Get the discovery map file defined in the environment."""
    return env.get(
        ENV_NAME__LOCAL_FILE_DISCOVERY_MAP, DEFAULT__LOCAL_FILE_DISCOVERY_MAP,
    )


def get_templates_file(env: Dict[str, str]) -> str:
    """Get the template file defined in the environment"""
    return env.get(
        ENV_NAME__LOCAL_FILE_TEMPLATES, DEFAULT__LOCAL_FILE_TEMPLATE,
    )
