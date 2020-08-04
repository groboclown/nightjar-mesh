
"""
Configures the program for use with AWS based on standard settings.  It also scans the
environment for the configuration.
"""

from typing import Dict, Sequence, Optional
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
ENV__REQUIRED_TAG = 'NJ_DMECS_REQUIRED_TAG'
ENV__REQUIRED_TAG_VALUE = 'NJ_DMECS_REQUIRED_TAG_VALUE'


class Config:
    """Extension point configuration."""
    __slots__ = (
        'clusters', 'aws_config', 'test_mode',
        'namespace', 'service', 'color',
        'required_tag_name', 'required_tag_value',
    )

    def __init__(self, env: Dict[str, str]) -> None:
        self.clusters = get_clusters(env)
        self.namespace = get_namespace(env)
        self.service = get_service(env)
        self.color = get_color(env)
        self.aws_config: Dict[str, str] = get_aws_config(env)
        self.test_mode = False
        self.required_tag_name = get_required_tag_name(env)
        self.required_tag_value = get_required_tag_value(env)


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


def get_required_tag_name(env: Dict[str, str]) -> Optional[str]:
    """Get the environment required tag name."""
    return env.get(ENV__REQUIRED_TAG, None)


def get_required_tag_value(env: Dict[str, str]) -> Optional[str]:
    """Get the environment required tag value."""
    return env.get(ENV__REQUIRED_TAG_VALUE, None)


def get_aws_config(env: Dict[str, str]) -> Dict[str, str]:
    """Create the AWS config."""
    ret: Dict[str, str] = {}
    for key, value in env.items():
        if key.startswith('AWS_'):
            ret[key] = value
    return ret
