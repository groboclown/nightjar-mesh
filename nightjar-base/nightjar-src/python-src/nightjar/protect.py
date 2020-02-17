
"""
Protection levels for service routes.

Routes are allowed to have any name for protection, but it must conform to the
`is_valid_route_protection` call.
"""

from typing import NewType, Optional, Any, cast
import re

RouteProtection = NewType('RouteProtection', str)

ROUTE_PROTECTION_RE = re.compile(r'^[0-9a-zA-Z][0-9a-zA-Z_\-]*$')


def is_valid_route_protection(protection: Any) -> bool:
    """Checks if the protection text is a valid protection name.  Returns True if valid, False if not."""
    if not isinstance(protection, str):
        return False
    return ROUTE_PROTECTION_RE.match(protection) is not None


def as_route_protection(protection: Any) -> RouteProtection:
    """Converts the protection text into a protection type; raises ValueError if it doesn't conform to
    the standard."""
    if not is_valid_route_protection(protection):
        raise ValueError('invalid protection format: `{0}`'.format(protection))
    return cast(RouteProtection, protection)


def as_optional_route_protection(protection: Optional[str]) -> Optional[RouteProtection]:
    """Converts the protection text into an optional protection type; raises ValueError if it doesn't conform to
    the standard."""
    if protection is None:
        return None
    return as_route_protection(protection)
