
from typing import Any
import sys

DEBUG_ON = True


def debug(msg: str, **args: Any) -> None:
    if DEBUG_ON:
        sys.stderr.write("DEBUG: {0}\n".format(msg.format(**args)))


def note(msg: str, **args: Any) -> None:
    sys.stderr.write("NOTE: {0}\n".format(msg.format(**args)))


def warn(msg: str, **args: Any) -> None:
    sys.stderr.write("WARNING: {0}\n".format(msg.format(**args)))


def fatal(msg: str, **args: Any) -> None:
    # Fatal errors quit right away.
    raise Exception(msg.format(**args))
