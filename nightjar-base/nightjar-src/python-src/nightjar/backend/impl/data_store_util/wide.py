
"""
Functionality for creating S3 paths and parsing paths.
"""

from typing import List, Optional, Union
from ...api.data_store.abc_backend import (
    Entity,
    ConfigEntity,
    TemplateEntity,
    ServiceIdConfigEntity,
    as_service_id_config_entity,
    ServiceColorTemplateEntity,
    as_service_color_template_entity,
    GatewayConfigEntity,
    as_gateway_config_entity,
    NamespaceTemplateEntity,
    as_namespace_template_entity,
    SUPPORTED_ACTIVITIES,
    ACTIVITY_PROXY_CONFIGURATION,
    ACTIVITY_TEMPLATE_DEFINITION,
)
from ....protect import RouteProtection, as_route_protection, is_valid_route_protection

DEFAULT_SERVICE_NAME = '__default__'
DEFAULT_COLOR_NAME = '__default__'
DEFAULT_NAMESPACE_NAME = '__default__'
DEFAULT_PROTECTION_NAME = 'default'


def get_entity_path(version: str, entity: Entity) -> List[str]:
    """Get the standard path for the version + entity"""
    nte = as_namespace_template_entity(entity)
    if nte:
        return get_namespace_template_path(version, nte)
    sct = as_service_color_template_entity(entity)
    if sct:
        return get_service_color_template_path(version, sct)
    gce = as_gateway_config_entity(entity)
    if gce:
        return get_gateway_config_path(version, gce)
    sce = as_service_id_config_entity(entity)
    assert sce
    return get_service_id_config_path(version, sce)


def parse_template_path(version: str, path: List[str]) -> Optional[TemplateEntity]:
    """Convert the version + path into a template entity."""
    namespace = parse_namespace_template_path(version, path)
    if namespace:
        return namespace
    service = parse_service_color_template_path(version, path)
    if service:
        return service
    return None


def parse_config_path(version: str, path: List[str]) -> Optional[ConfigEntity]:
    """Convert the version + path into a config entity."""
    namespace = parse_gateway_config_path(version, path)
    if namespace:
        return namespace
    service = parse_service_id_config_path(version, path)
    if service:
        return service
    return None


def get_namespace_template_prefix(version: str) -> List[str]:
    """Get the prefix path parts for the namespace template + version."""
    return [
        *get_activity_prefix(version, ACTIVITY_TEMPLATE_DEFINITION),
        'gateway',
    ]


def get_namespace_template_path(version: str, entity: NamespaceTemplateEntity) -> List[str]:
    """Get the path parts for the namespace template + version."""
    return [
        *get_namespace_template_prefix(version),
        entity.namespace or DEFAULT_NAMESPACE_NAME,
        get_protection_path_name(entity.protection),
        entity.purpose,
    ]


def parse_namespace_template_path(
        version: str, path: List[str],
) -> Optional[NamespaceTemplateEntity]:
    """Parse the version + path parts into a namespace template entity."""
    parts = get_path_after_prefix(get_namespace_template_prefix(version), 3, path)
    if not parts:
        return None
    namespace, protection_str, purpose = parts
    protection = parse_protection(protection_str)
    if isinstance(protection, bool):
        return None
    return NamespaceTemplateEntity(
        parse_namespace(namespace),
        protection,
        purpose,
    )


def get_service_color_template_prefix(version: str) -> List[str]:
    """Get the prefix path parts for the service/color template + version."""
    return [
        *get_activity_prefix(version, ACTIVITY_TEMPLATE_DEFINITION),
        'service',
    ]


def get_service_color_template_path(version: str, entity: ServiceColorTemplateEntity) -> List[str]:
    """Get the path parts for the service/color template + version."""
    return [
        *get_service_color_template_prefix(version),
        entity.namespace or DEFAULT_NAMESPACE_NAME,
        entity.service or DEFAULT_SERVICE_NAME,
        entity.color or DEFAULT_COLOR_NAME,
        entity.purpose,
    ]


def parse_service_color_template_path(
        version: str, path: List[str],
) -> Optional[ServiceColorTemplateEntity]:
    """Parse the version + path parts into a service/color template entity."""
    parts = get_path_after_prefix(get_service_color_template_prefix(version), 4, path)
    if not parts:
        return None
    namespace, service, color, purpose = parts
    return ServiceColorTemplateEntity(
        parse_namespace(namespace),
        parse_service(service),
        parse_color(color),
        purpose,
    )


def get_gateway_config_prefix(version: str) -> List[str]:
    """Get the prefix path parts for the gateway config + version."""
    return [
        *get_activity_prefix(version, ACTIVITY_PROXY_CONFIGURATION),
        'gateway',
    ]


def get_gateway_config_path(version: str, entity: GatewayConfigEntity) -> List[str]:
    """Get the path parts for the gateway config + version."""
    # namespace_id cannot be None or empty
    assert entity.namespace_id
    return [
        *get_gateway_config_prefix(version),
        entity.namespace_id,
        get_protection_path_name(entity.protection),
        entity.purpose,
    ]


def parse_gateway_config_path(version: str, path: List[str]) -> Optional[GatewayConfigEntity]:
    """Parse the version + path parts into a gateway config entity."""
    parts = get_path_after_prefix(get_gateway_config_prefix(version), 3, path)
    if not parts:
        return None
    namespace, protection_str, purpose = parts
    protection = parse_protection(protection_str)
    if not is_valid_route_protection(protection):
        return None
    return GatewayConfigEntity(
        namespace,
        as_route_protection(protection),
        purpose,
    )


def get_service_id_config_prefix(version: str) -> List[str]:
    """Get the prefix path parts for the service id config + version."""
    return [
        *get_activity_prefix(version, ACTIVITY_PROXY_CONFIGURATION),
        'service',
    ]


def get_service_id_config_path(version: str, entity: ServiceIdConfigEntity) -> List[str]:
    """Get the path parts for the service id config + version."""
    return [
        *get_service_id_config_prefix(version),
        entity.namespace_id,
        entity.service_id,
        entity.service,
        entity.color,
        entity.purpose,
    ]


def parse_service_id_config_path(version: str, path: List[str]) -> Optional[ServiceIdConfigEntity]:
    """Parse the version + path parts into a service id config entity."""
    parts = get_path_after_prefix(get_service_id_config_prefix(version), 5, path)
    if not parts:
        # debug('Insufficient parts for a service_id: {p}', p=path)
        return None
    namespace, service_id, service, color, purpose = parts
    return ServiceIdConfigEntity(
        namespace,
        service_id,
        service,
        color,
        purpose,
    )


def get_protection_path_name(protection: Optional[RouteProtection]) -> str:
    """Get the protection's path name."""
    if protection is None:
        return DEFAULT_PROTECTION_NAME
    return protection


def parse_protection(part: str) -> Union[bool, Optional[RouteProtection]]:
    """Parse the protection path part."""
    if part == DEFAULT_PROTECTION_NAME:
        return None
    if not is_valid_route_protection(part):
        return False
    return as_route_protection(part)


def parse_namespace(part: str) -> Optional[str]:
    """Parse the namespace path part."""
    if part == DEFAULT_NAMESPACE_NAME:
        return None
    return part


def parse_service(part: str) -> Optional[str]:
    """Parse the service path part."""
    if part == DEFAULT_SERVICE_NAME:
        return None
    return part


def parse_color(part: str) -> Optional[str]:
    """Parse the color path part."""
    if part == DEFAULT_COLOR_NAME:
        return None
    return part


def get_activity_prefix(version: str, activity: str) -> List[str]:
    """Get the prefix for the version + activity."""
    # Each activity is versioned, so have the activity/version path.
    return [
        'content',
        activity,
        version,
    ]


def get_path_after_prefix(
        prefix: List[str], expected_length: int, path: List[str],
) -> Optional[List[str]]:
    """Get the path parts after the prefix."""
    prefix_len = len(prefix)
    if len(path) < prefix_len:
        return None
    if path[0:prefix_len] != prefix:
        return None
    ret = path[prefix_len:]
    if len(ret) != expected_length:
        return None
    return ret


def parse_activity(version: str, path: List[str]) -> Optional[str]:
    """parse the activity from the path parts."""
    if len(path) < 3:
        return None
    if path[2] != version or path[0] != 'content':
        return None
    if path[1] in SUPPORTED_ACTIVITIES:
        return path[1]
    return None


def get_version_reference_prefix(activity: str) -> List[str]:
    """Get the version reference prefix for the activity."""
    return [
        'versions',
        activity,
    ]


def get_version_reference_path(activity: str, version: str) -> List[str]:
    """Get the version reference path for the activity."""
    return [
        *get_version_reference_prefix(activity),
        version,
    ]


def parse_version_reference_path(activity: str, path: List[str]) -> Optional[str]:
    """Parse the version path part for the activity."""
    parts = get_path_after_prefix(get_version_reference_prefix(activity), 1, path)
    if not parts:
        return None
    return parts[0]
