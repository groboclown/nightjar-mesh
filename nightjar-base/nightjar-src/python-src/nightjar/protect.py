
"""
Protection levels for service routes.

Routes are allowed to have any name for protection, but it must conform to the
`is_valid_route_protection` call.

Currently, the system only supports two modes of protection: public and private.
Public means that the published route will be available to all entry-points into
the mesh.  Private means that only services within the mesh can reach it.

Consideration has been made to allow other levels to represent intra-mesh
communication protection levels.  In this construct, the protection level acts
as a key, where the proxy needs to provide that protection level and the route
has that protection level.
"""

from typing import NewType, Sequence, Optional, Any, cast

RouteProtection = NewType('RouteProtection', str)

PROTECTION_PUBLIC = cast(RouteProtection, 'public')
PROTECTION_PRIVATE = cast(RouteProtection, 'private')

# Currently, only support these two levels.  Once a method for
# expressing the desired protection level on the gateways is
# established, then this can be expanded out.
_SUPPORTED_PROTECTIONS = (
    PROTECTION_PUBLIC,
    PROTECTION_PRIVATE,
)


def is_valid_route_protection(protection: Any) -> bool:
    """Checks if the protection text is a valid protection name.  Returns True if valid, False if not."""
    if not isinstance(protection, str):
        return False
    # Once the protection scheme is established, this can be loosened.
    # return protection.strip() == protection and len(protection) > 0
    return protection in _SUPPORTED_PROTECTIONS


def as_route_protection(protection: Any) -> RouteProtection:
    """Converts the protection text into a protection type; raises ValueError
    if it doesn't conform to the standard.  The namespace is required, because
    private protections are converted to namespace-specific protections."""
    if not is_valid_route_protection(protection):
        raise ValueError('invalid protection format: `{0}`'.format(protection))
    assert isinstance(protection, str)
    return cast(RouteProtection, protection)


def as_optional_route_protection(protection: Optional[str]) -> Optional[RouteProtection]:
    """Converts the protection text into an optional protection type; raises ValueError if it doesn't conform to
    the standard."""
    if protection is None:
        return None
    return as_route_protection(protection)


def can_use_route(requested_protection: Sequence[RouteProtection], route_protection: RouteProtection) -> bool:
    if route_protection == PROTECTION_PUBLIC:
        return True

    # If both are private, then it's visible.
    # If one is intra-mesh and the other is private,
    #   then it's not visible.
    # If requested is public and the other isn't,
    #   then it's not visible.

    return route_protection in requested_protection
