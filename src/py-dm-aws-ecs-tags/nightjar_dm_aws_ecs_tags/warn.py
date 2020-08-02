
"""Produce warning and error messages."""

from typing import Any
import sys


def warning(source: str, message: str, **kwargs: Any) -> None:
    """Produce a warning message."""
    log('WARNING', source, message, **kwargs)


def log(level: str, source: str, message: str, **kwargs: Any) -> None:
    """Produce a log message."""
    sys.stderr.write(
        '[nightjar_dm_aws_ecs_tags: {0}] {1}: {2}\n'.format(
            level, source, message.format(**kwargs),
        )
    )
