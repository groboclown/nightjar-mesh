
"""
Message reporting mechanism.  Avoids using the Python logging for a simpler approach.
"""

from typing import Any
import sys

DEBUG_ON = True


def debug(msg: str, **args: Any) -> None:
    """Report a debug message, if debug messages are turned on."""
    if DEBUG_ON:
        sys.stderr.write("DEBUG: {0}\n".format(msg.format(**args)))


def note(msg: str, **args: Any) -> None:
    """Report a note message."""
    sys.stderr.write("NOTE: {0}\n".format(msg.format(**args)))


def warn(msg: str, **args: Any) -> None:
    """Report a warning."""
    sys.stderr.write("WARNING: {0}\n".format(msg.format(**args)))


def fatal(msg: str, **args: Any) -> None:
    """Report a fatal error.  Fatal errors are, well, fatal, and cause an immediate exit."""
    raise Exception(msg.format(**args))
