
"""
Configures the program for use with AWS based on standard settings.  It also scans the
environment for the configuration.
"""

from typing import Dict, Sequence
import os
from . import ecs

ENV__AWS_CLUSTERS = 'NJ_DMECS_AWS_CLUSTERS'
DEFAULT_CLUSTER_NAME = 'default'
ENV__NAMESPACE = 'NJ_NAMESPACE'
DEFAULT_NAMESPACE = 'default'
ENV__SERVICE = 'NJ_SERVICE'
DEFAULT_SERVICE = 'default'
ENV__COLOR = 'NJ_COLOR'
DEFAULT_COLOR = 'default'


class Config:
    """Extension point configuration."""
    __slots__ = (
        'clusters', 'aws_config', 'test_mode',
        'namespace', 'service', 'color',
    )

    def __init__(self, env: Dict[str, str]) -> None:
        self.clusters = get_clusters(env)
        self.namespace = get_namespace(env)
        self.service = get_service(env)
        self.color = get_color(env)
        self.aws_config: Dict[str, str] = {}
        self.test_mode = False


def create_configuration() -> Config:
    """Setup the configuration."""
    config = Config(dict(os.environ))
    ecs.set_aws_config(config.aws_config)
    return config


def get_clusters(env: Dict[str, str]) -> Sequence[str]:
    """Get the AWS clusters to scan."""
    contents = env.get(ENV__AWS_CLUSTERS, DEFAULT_CLUSTER_NAME)
    return [
        name.strip()
        for name in contents.split(',')
    ]


def get_namespace(env: Dict[str, str]) -> str:
    """Get the environment namespace."""
    return env.get(ENV__NAMESPACE, DEFAULT_NAMESPACE)


def get_service(env: Dict[str, str]) -> str:
    """Get the environment service."""
    return env.get(ENV__SERVICE, DEFAULT_SERVICE)


def get_color(env: Dict[str, str]) -> str:
    """Get the environment service color."""
    return env.get(ENV__COLOR, DEFAULT_COLOR)
