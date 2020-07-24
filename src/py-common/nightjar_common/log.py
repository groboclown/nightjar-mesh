
"""
Simple logging tools.
"""

from typing import Any
import os
import sys
from .consts import TRUE_VALUES


EXECUTE_MODEL = 'nightjar-not-initialized'
DEBUG_ON = os.environ.get('DEBUG', 'false') in TRUE_VALUES


def debug(msg: str, **kwargs: Any) -> None:
    """Debug messages."""
    if DEBUG_ON:
        log('DEBUG', msg, **kwargs)


def warning(msg: str, **kwargs: Any) -> None:
    """Debug messages."""
    log('WARN', msg, **kwargs)


def log(mode: str, msg: str, **kwargs: Any) -> None:
    """Print a log message."""
    sys.stderr.write('[{0} :: {1}] {2}\n'.format(EXECUTE_MODEL, mode, msg.format(**kwargs)))
