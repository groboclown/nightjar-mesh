
"""Constant values... and other things."""

from typing import Any
import os
import sys


DATA_FILE_EXTENSION = '.data'
META_FILE_EXTENSION = '.meta'
FILE_EXTENSION_LENGTH = 5

DEBUG = os.environ.get('DEBUG') == 'true'


def get_version_from_data_key_name(key: str) -> str:
    """Extract the version from the key name for the given data or meta."""
    assert key.endswith(DATA_FILE_EXTENSION) or key.endswith(META_FILE_EXTENSION)
    if '/' in key:
        key = key[key.rindex('/') + 1:]
    return key[:-FILE_EXTENSION_LENGTH]


def is_data_file(key: str) -> bool:
    """Is the key a data file?"""
    return key.endswith(DATA_FILE_EXTENSION)


def is_meta_file(key: str) -> bool:
    """Is the key a data file?"""
    return key.endswith(META_FILE_EXTENSION)


def debug(message: str, **kwargs: Any) -> None:
    """Debug logging."""
    if DEBUG:
        log('DEBUG', message, **kwargs)


def log(level: str, message: str, **kwargs: Any) -> None:
    """Log information to stderr."""
    sys.stderr.write('[nightjar-ds_aws_s3 :: {0}] {1}\n'.format(
        level, message.format(**kwargs)
    ))
