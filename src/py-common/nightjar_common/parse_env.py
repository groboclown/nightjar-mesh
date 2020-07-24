
"""

"""

from typing import Dict
from .log import warning
from .consts import TRUE_VALUES, FALSE_VALUES


def env_as_int(
        env: Dict[str, str], key: str, default: int,
) -> int:
    """Convert an environment value to an integer."""
    value = env.get(key)
    if value:
        try:
            return int(value)
        except ValueError:
            warning(
                'Environment variable {key} must be an integer, '
                'but found {value}; using {default} instead.',
                key=key,
                value=value,
                default=default,
            )
    return default


def env_as_bool(
        env: Dict[str, str], key: str, default: bool,
) -> bool:
    """Convert an environment value to an integer."""
    value = env.get(key)
    if value:
        value = value.lower()
        if value in TRUE_VALUES:
            return True
        if value in FALSE_VALUES:
            return False
        warning(
            'Environment variable {key} must be a true/false value, '
            'but found {value}; using {default} instead.',
            key=key,
            value=value,
            default=default,
        )
    return default
