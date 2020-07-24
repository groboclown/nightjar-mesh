
"""
Configuration definition and loading.
"""

from typing import Dict
import os

ENV__BASE_DIR = 'NJ_DMLOCAL_BASE_DIR'
DEFAULT_BASE_DIR = '/usr/share/nightjar/discovery-map'
ENV__NAMESPACE = 'NJ_NAMESPACE'
DEFAULT_NAMESPACE = 'default'
ENV__SERVICE = 'NJ_SERVICE'
DEFAULT_SERVICE = 'default'
ENV__COLOR = 'NJ_COLOR'
DEFAULT_COLOR = 'default'


class Config:
    """Local configuration."""
    __slots__ = ('base_dir', 'namespace', 'service', 'color',)

    def __init__(self, env: Dict[str, str]) -> None:
        self.base_dir = get_base_dir(env)
        self.namespace = get_namespace(env)
        self.service = get_service(env)
        self.color = get_color(env)


def create_configuration() -> Config:
    """Create and load the configuration."""
    return Config(dict(os.environ))


def get_base_dir(env: Dict[str, str]) -> str:
    """Get the base directory defined in the environment."""
    return env.get(ENV__BASE_DIR, DEFAULT_BASE_DIR)


def get_namespace(env: Dict[str, str]) -> str:
    """Get the environment namespace."""
    return env.get(ENV__NAMESPACE, DEFAULT_NAMESPACE)


def get_service(env: Dict[str, str]) -> str:
    """Get the environment service."""
    return env.get(ENV__SERVICE, DEFAULT_SERVICE)


def get_color(env: Dict[str, str]) -> str:
    """Get the environment service color."""
    return env.get(ENV__COLOR, DEFAULT_COLOR)
