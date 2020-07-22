
"""
Manage the reading and writing of local files.
"""

from typing import Iterable, Tuple, List, Dict, Optional, Any
import os
import json
from ...backend.api.data_store import (
    GatewayConfigEntity,
    ServiceIdConfigEntity,
    TemplateEntity,
    NamespaceTemplateEntity,
    as_namespace_template_entity,
    ServiceColorTemplateEntity,
    as_service_color_template_entity,
)
from ...protect import RouteProtection, as_route_protection
from ...msg import warn

TEMPLATE_DESCRIPTION_FILENAME = 'templates.json'
CONFIG_DESCRIPTION_FILENAME = 'configured.json'


def find_templates(src_dir: str) -> Iterable[Tuple[TemplateEntity, str]]:
    """
    Searches the source directory for child directories that contain the template description file.
    """
    if not os.path.isdir(src_dir):
        warn("Not a directory: {s}", s=src_dir)
        return tuple()

    ret: List[Tuple[TemplateEntity, str]] = []
    for name in os.listdir(src_dir):
        if name.startswith('.'):
            continue
        dir_name = os.path.join(src_dir, name)
        if not os.path.isdir(dir_name):
            continue
        description_filename = os.path.join(dir_name, TEMPLATE_DESCRIPTION_FILENAME)
        if not os.path.isfile(description_filename):
            continue
        base_entity = read_template_description(description_filename)
        if not base_entity:
            warn('Invalid template description file: {f}', f=description_filename)
            continue
        for res in collect_template_files(base_entity, dir_name):
            ret.append(res)
    return ret


def collect_template_files(
        base_entity: TemplateEntity, directory: str,
) -> Iterable[Tuple[TemplateEntity, str]]:
    """Collect all the entity files from the directory, and parse them."""
    n_s = as_namespace_template_entity(base_entity)
    s_c = as_service_color_template_entity(base_entity)
    assert n_s or s_c
    for name in os.listdir(directory):
        if name.startswith('.') or name == TEMPLATE_DESCRIPTION_FILENAME:
            continue
        filename = os.path.join(directory, name)
        if not os.path.isfile(filename):
            continue
        with open(filename, 'r') as f:
            contents = f.read()
        if n_s:
            yield NamespaceTemplateEntity(n_s.namespace, n_s.protection, name), contents
        if s_c:
            yield ServiceColorTemplateEntity(s_c.namespace, s_c.service, s_c.color, name), contents


def write_namespace_template_entity(
        base_dir: str, entity: NamespaceTemplateEntity, contents: str,
) -> None:
    """Write the entity to a file."""
    sub_dir_name = 'namespace-{n}-{p}'.format(
        n=entity.namespace or 'default',
        p=get_protection_part_name(entity.protection)
    )
    out_dir = os.path.join(base_dir, sub_dir_name)
    os.makedirs(out_dir, exist_ok=True)
    description_file = os.path.join(out_dir, CONFIG_DESCRIPTION_FILENAME)
    if not os.path.exists(description_file):
        with open(description_file, 'w') as f:
            json.dump({
                "type": "namespace",
                "namespace": entity.namespace,
                "is_public": entity.protection,
            }, f)
    content_file = os.path.join(out_dir, entity.purpose)
    with open(content_file, 'w') as f:
        f.write(contents)


def write_gateway_config_entity(
        base_dir: str, entity: GatewayConfigEntity, contents: str,
) -> None:
    """Write the entity to a file."""
    sub_dir_name = 'gateway-{n}-{p}'.format(
        n=entity.namespace_id, p=get_protection_part_name(entity.protection),
    )
    out_dir = os.path.join(base_dir, sub_dir_name)
    os.makedirs(out_dir, exist_ok=True)
    description_file = os.path.join(out_dir, CONFIG_DESCRIPTION_FILENAME)
    if not os.path.exists(description_file):
        with open(description_file, 'w') as f:
            json.dump({
                "type": "gateway",
                "namespace_id": entity.namespace_id,
                "protection": entity.protection,
            }, f)
    content_file = os.path.join(out_dir, entity.purpose)
    with open(content_file, 'w') as f:
        f.write(contents)


def write_service_id_config_entity(
        base_dir: str, entity: ServiceIdConfigEntity, contents: str,
) -> None:
    """Write the entity to a file."""
    sub_dir_name = 'service_id-{n}-{sid}-{s}-{c}'.format(
        n=entity.namespace_id, sid=entity.service_id,
        s=entity.service, c=entity.color,
    )
    out_dir = os.path.join(base_dir, sub_dir_name)
    os.makedirs(out_dir, exist_ok=True)
    description_file = os.path.join(out_dir, CONFIG_DESCRIPTION_FILENAME)
    if not os.path.exists(description_file):
        with open(description_file, 'w') as f:
            json.dump({
                "type": "service-id",
                "namespace_id": entity.namespace_id,
                "service_id": entity.service_id,
                "service": entity.service,
                "color": entity.color,
            }, f)
    content_file = os.path.join(out_dir, entity.purpose)
    with open(content_file, 'w') as f:
        f.write(contents)


def write_service_color_template_entity(
        base_dir: str, entity: ServiceColorTemplateEntity, contents: str,
) -> None:
    """Write the entity contents to a file."""
    sub_dir_name = 'service-{n}-{s}-{c}'.format(
        n=entity.namespace or 'default',
        s=entity.service or 'default', c=entity.color or 'default',
    )
    out_dir = os.path.join(base_dir, sub_dir_name)
    os.makedirs(out_dir, exist_ok=True)
    description_file = os.path.join(out_dir, CONFIG_DESCRIPTION_FILENAME)
    if not os.path.exists(description_file):
        with open(description_file, 'w') as f:
            json.dump({
                "type": "service-color",
                "namespace": entity.namespace,
                "service": entity.service,
                "color": entity.color,
            }, f)
    content_file = os.path.join(out_dir, entity.purpose)
    with open(content_file, 'w') as f:
        f.write(contents)


def read_template_description(filename: str) -> Optional[TemplateEntity]:
    """
    Reads the template description file, and returns None if it isn't valid, or a template entity
    (with the purpose left blank) if it is.
    """
    with open(filename, 'r') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        warn('template descriptor must be a JSon formatted dictionary: {f}', f=filename)
        return None

    template_type = data.get('type')
    namespace = data.get('namespace', data.get('namespace-id', data.get('namespace_id', None)))
    protection = parse_protection(data)
    service = data.get('service', None)
    color = data.get('color', None)
    if template_type in ('namespace', 'gateway'):
        return NamespaceTemplateEntity(namespace, protection, '')
    if template_type in ('service', 'service-color', 'service_color', 'service/color'):
        return ServiceColorTemplateEntity(namespace, service, color, '')
    warn('Unsupported template type: {t}', t=template_type)
    return None


def parse_protection(data: Dict[str, Any]) -> Optional[RouteProtection]:
    """Figure out the protection level from the dictionary of values."""
    protection = data.get('protection', None)
    if protection in (None, 'default'):
        return None
    return as_route_protection(protection)


def get_protection_part_name(protection: Optional[RouteProtection]) -> str:
    """The protection name, replaced with the default if None."""
    return protection or 'default'
