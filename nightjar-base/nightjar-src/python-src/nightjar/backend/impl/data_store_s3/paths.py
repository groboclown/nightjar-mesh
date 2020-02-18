
"""
Functionality for creating S3 paths and parsing paths.
"""

from typing import Optional, Union
from .config import S3EnvConfig
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


def get_entity_path(config: S3EnvConfig, version: str, entity: Entity) -> str:
    nte = as_namespace_template_entity(entity)
    if nte:
        return get_namespace_template_path(config, version, nte)
    sct = as_service_color_template_entity(entity)
    if sct:
        return get_service_color_template_path(config, version, sct)
    gce = as_gateway_config_entity(entity)
    if gce:
        return get_gateway_config_path(config, version, gce)
    sce = as_service_id_config_entity(entity)
    assert sce
    return get_service_id_config_path(config, version, sce)


def parse_template_path(config: S3EnvConfig, version: str, path: str) -> Optional[TemplateEntity]:
    namespace = parse_namespace_template_path(config, version, path)
    if namespace:
        return namespace
    service = parse_service_color_template_path(config, version, path)
    if service:
        return service
    return None


def parse_config_path(config: S3EnvConfig, version: str, path: str) -> Optional[ConfigEntity]:
    namespace = parse_gateway_config_path(config, version, path)
    if namespace:
        return namespace
    service = parse_service_id_config_path(config, version, path)
    if service:
        return service
    return None


def get_namespace_template_prefix(config: S3EnvConfig, version: str) -> str:
    return '{pre}gateway'.format(pre=get_activity_prefix(config, version, ACTIVITY_TEMPLATE_DEFINITION))


def get_namespace_template_path(
        config: S3EnvConfig, version: str,
        entity: NamespaceTemplateEntity,
) -> str:
    return '{pre}gateway/{n}/{pr}/{p}'.format(
        pre=get_activity_prefix(config, version, entity.activity),
        n=entity.namespace or DEFAULT_NAMESPACE_NAME,
        pr=get_protection_path_name(entity.protection),
        p=entity.purpose,
    )


def parse_namespace_template_path(config: S3EnvConfig, version: str, path: str) -> Optional[NamespaceTemplateEntity]:
    prefix = get_activity_prefix(config, version, ACTIVITY_TEMPLATE_DEFINITION)
    if not path.startswith(prefix):
        return None
    parts = path[len(prefix):].split('/')
    if len(parts) != 4:
        return None
    gw, namespace, protection_str, purpose = parts
    protection = parse_protection(protection_str)
    if isinstance(protection, bool) or gw != 'gateway':
        return None
    return NamespaceTemplateEntity(
        parse_namespace(namespace),
        protection,
        purpose
    )


def get_service_color_template_prefix(config: S3EnvConfig, version: str) -> str:
    return '{pre}service'.format(pre=get_activity_prefix(config, version, ACTIVITY_TEMPLATE_DEFINITION))


def get_service_color_template_path(
        config: S3EnvConfig, version: str,
        entity: ServiceColorTemplateEntity,
) -> str:
    return '{pre}service/{n}/{s}/{c}/{p}'.format(
        pre=get_activity_prefix(config, version, entity.activity),
        n=entity.namespace or DEFAULT_NAMESPACE_NAME,
        s=entity.service or DEFAULT_SERVICE_NAME,
        c=entity.color or DEFAULT_COLOR_NAME,
        p=entity.purpose,
    )


def parse_service_color_template_path(
        config: S3EnvConfig, version: str, path: str
) -> Optional[ServiceColorTemplateEntity]:
    prefix = get_activity_prefix(config, version, ACTIVITY_TEMPLATE_DEFINITION)
    if not path.startswith(prefix):
        return None
    parts = path[len(prefix):].split('/')
    if len(parts) != 5:
        return None
    sc, namespace, service, color, purpose = parts
    if sc != 'service':
        return None
    return ServiceColorTemplateEntity(
        parse_namespace(namespace),
        parse_service(service),
        parse_color(color),
        purpose
    )


def get_gateway_config_prefix(config: S3EnvConfig, version: str) -> str:
    return '{pre}gateway/'.format(pre=get_activity_prefix(config, version, ACTIVITY_PROXY_CONFIGURATION))


def get_gateway_config_path(
        config: S3EnvConfig, version: str,
        entity: GatewayConfigEntity,
) -> str:
    assert entity.namespace_id
    return '{pre}gateway/{n}/{pr}/{p}'.format(
        pre=get_activity_prefix(config, version, entity.activity),
        n=entity.namespace_id,
        pr=get_protection_path_name(entity.protection),
        p=entity.purpose,
    )


def parse_gateway_config_path(config: S3EnvConfig, version: str, path: str) -> Optional[GatewayConfigEntity]:
    prefix = get_activity_prefix(config, version, ACTIVITY_PROXY_CONFIGURATION)
    if not path.startswith(prefix):
        return None
    parts = path[len(prefix):].split('/')
    if len(parts) != 4:
        return None
    gw, namespace, protection_str, purpose = parts
    protection = parse_protection(protection_str)
    if not is_valid_route_protection(protection) or gw != 'gateway':
        return None
    return GatewayConfigEntity(
        namespace,
        as_route_protection(protection),
        purpose
    )


def get_service_id_config_prefix(config: S3EnvConfig, version: str) -> str:
    return '{pre}service/'.format(pre=get_activity_prefix(config, version, ACTIVITY_PROXY_CONFIGURATION))


def get_service_id_config_path(
        config: S3EnvConfig, version: str,
        entity: ServiceIdConfigEntity,
) -> str:
    return '{pre}service/{n}/{sid}/{s}/{c}/{p}'.format(
        pre=get_activity_prefix(config, version, entity.activity),
        n=entity.namespace_id,
        sid=entity.service_id,
        s=entity.service,
        c=entity.color,
        p=entity.purpose,
    )


def parse_service_id_config_path(
        config: S3EnvConfig, version: str, path: str
) -> Optional[ServiceIdConfigEntity]:
    prefix = get_activity_prefix(config, version, ACTIVITY_PROXY_CONFIGURATION)
    if not path.startswith(prefix):
        # debug('Not right activity: {pre} ({s})', pre=prefix, s=path)
        return None
    parts = path[len(prefix):].split('/')
    if len(parts) != 6:
        # debug('Insufficient parts for a service_id: {p} ({s})', p=parts, s=path)
        return None
    sc, namespace, service_id, service, color, purpose = parts
    if sc != 'service':
        # debug('Parts dont start with service: {p} ({s})', p=parts, s=path)
        return None
    return ServiceIdConfigEntity(
        namespace,
        service_id,
        service,
        color,
        purpose
    )


def get_protection_path_name(protection: Optional[RouteProtection]) -> str:
    if protection is None:
        return DEFAULT_PROTECTION_NAME
    return protection


def parse_protection(part: str) -> Union[bool, Optional[RouteProtection]]:
    if part == DEFAULT_PROTECTION_NAME:
        return None
    if not is_valid_route_protection(part):
        return False
    return as_route_protection(part)


def parse_namespace(part: str) -> Optional[str]:
    if part == DEFAULT_NAMESPACE_NAME:
        return None
    return part


def parse_service(part: str) -> Optional[str]:
    if part == DEFAULT_SERVICE_NAME:
        return None
    return part


def parse_color(part: str) -> Optional[str]:
    if part == DEFAULT_COLOR_NAME:
        return None
    return part


def get_activity_prefix(config: S3EnvConfig, version: str, activity: str) -> str:
    # Each activity is versioned, so have the activity/version path.
    return '{bp}/content/{a}/{v}/'.format(
        bp=config.base_path,
        v=version,
        a=activity,
    )


def parse_activity(config: S3EnvConfig, version: str, path: str) -> Optional[str]:
    if not path.startswith(config.base_path):
        return None
    parts = path[len(config.base_path) + 1:].split('/')
    if len(parts) < 3:
        return None
    if version != parts[2] or 'content' != parts[0]:
        return None
    if parts[1] in SUPPORTED_ACTIVITIES:
        return parts[1]
    return None


def get_version_reference_path(config: S3EnvConfig, activity: str, version: str) -> str:
    return '{bp}/versions/{a}/{v}'.format(
        bp=config.base_path,
        a=activity,
        v=version,
    )


def get_version_reference_prefix(config: S3EnvConfig, activity: str) -> str:
    return '{bp}/versions/{a}/'.format(
        bp=config.base_path,
        a=activity,
    )


def parse_version_reference_path(config: S3EnvConfig, activity: str, path: str) -> Optional[str]:
    prefix = get_version_reference_prefix(config, activity)
    if not path.startswith(prefix):
        return None
    v = path[len(prefix):]
    if not v:
        return None
    return v
