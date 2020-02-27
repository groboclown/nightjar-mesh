
from typing import Tuple, Optional, Iterable, List
import os
import json
import shutil
from .config import LocalEnvConfig
from ..data_store_util import wide
from ...api.data_store import ConfigEntity
from ...api.data_store.abc_backend import (
    AbcDataStoreBackend,
    Entity,
    SUPPORTED_ACTIVITIES,
    ServiceIdConfigEntity,
    ServiceColorTemplateEntity,
    GatewayConfigEntity,
    NamespaceTemplateEntity,
    TemplateEntity,
    as_service_id_config_entity,
    as_gateway_config_entity,
    as_service_color_template_entity,
    as_namespace_template_entity,
)
from ....protect import RouteProtection


class LocalFileBackend(AbcDataStoreBackend):
    """
    This is a "wide" model, where it writes each purpose as its own file.  The only record
    of where things are and what they are is based on the directory path.  This is to help
    with debugging.
    """
    def __init__(self, config: LocalEnvConfig) -> None:
        self.config = config

    def get_active_version(self, activity: str) -> str:
        version_number = self._get_active_version(activity)
        if version_number < 0:
            return activity + '-first'
        return activity + '-' + str(version_number)

    def start_changes(self, activity: str) -> str:
        active = self._get_active_version(activity)
        return activity + '-' + str(active + 1)

    def commit_changes(self, version: str) -> None:
        activity, version_num = LocalFileBackend._parse_version(version)
        self._write_active_version(activity, version_num)

    def rollback_changes(self, version: str) -> None:
        activity, version_num = LocalFileBackend._parse_version(version)
        version_dir = self._get_path(wide.get_activity_prefix(str(version_num), activity))
        if os.path.isdir(version_dir):
            shutil.rmtree(version_dir, True)

    def download(self, version: str, entity: Entity) -> str:
        activity, version_num = LocalFileBackend._parse_version(version)
        file_path = self._get_path(wide.get_entity_path(str(version_num), entity))
        if not file_path:
            raise ValueError('no such file at ' + file_path)
        with open(file_path, 'r') as f:
            return f.read()

    def upload(self, version: str, entity: Entity, contents: str) -> None:
        activity, version_num = LocalFileBackend._parse_version(version)
        file_path = self._get_path(wide.get_entity_path(str(version_num), entity))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(contents)

    def get_template_entities(self, version: str) -> Iterable[TemplateEntity]:
        for entity in self.get_all_entities(version):
            if isinstance(entity, TemplateEntity):
                yield entity

    def get_config_entities(self, version: str) -> Iterable[ConfigEntity]:
        for entity in self.get_all_entities(version):
            if isinstance(entity, ConfigEntity):
                yield entity

    def get_namespace_template_entities(
            self, version: str, namespace: Optional[str] = None,
            protection: Optional[RouteProtection] = None, purpose: Optional[str] = None
    ) -> Iterable[NamespaceTemplateEntity]:
        for entity in self.get_all_entities(version):
            nte = as_namespace_template_entity(entity)
            if (
                nte
                and (not namespace or namespace == nte.namespace)
                and (not protection or protection == nte.protection)
                and (not purpose or purpose == nte.purpose)
            ):
                yield nte

    def get_gateway_config_entities(
            self, version: str, namespace: Optional[str] = None,
            protection: Optional[RouteProtection] = None, purpose: Optional[str] = None
    ) -> Iterable[GatewayConfigEntity]:
        for entity in self.get_all_entities(version):
            gce = as_gateway_config_entity(entity)
            if (
                gce
                and (not namespace or namespace == gce.namespace)
                and (not protection or protection == gce.protection)
                and (not purpose or purpose == gce.purpose)
            ):
                yield gce

    def get_service_color_template_entities(
            self, version: str, namespace: Optional[str] = None,
            service: Optional[str] = None, color: Optional[str] = None,
            purpose: Optional[str] = None
    ) -> Iterable[ServiceColorTemplateEntity]:
        for entity in self.get_all_entities(version):
            sct = as_service_color_template_entity(entity)
            if (
                sct
                and (not namespace or namespace == sct.namespace)
                and (not service or service == sct.service)
                and (not color or color == sct.color)
                and (not purpose or purpose == sct.purpose)
            ):
                yield sct

    def get_service_id_config_entities(
            self, version: str, namespace_id: Optional[str] = None,
            service_id: Optional[str] = None, service: Optional[str] = None,
            color: Optional[str] = None, purpose: Optional[str] = None
    ) -> Iterable[ServiceIdConfigEntity]:
        for entity in self.get_all_entities(version):
            sic = as_service_id_config_entity(entity)
            if (
                sic
                and (not namespace_id or namespace_id == sic.namespace_id)
                and (not service_id or service_id == sic.service_id)
                and (not service or service == sic.service)
                and (not color or color == sic.color)
                and (not purpose or purpose == sic.purpose)
            ):
                yield sic

    def get_all_entities(self, version: str) -> Iterable[Entity]:
        activity, version_num = LocalFileBackend._parse_version(version)
        version_str = str(version_num)
        base_entity_path = self._get_path(wide.get_activity_prefix(version_str, activity))
        for dirpath, dirnames, filenames in os.walk(base_entity_path):
            for filename in filenames:
                entity_path = self._split_path(os.path.join(dirpath, filename))
                config_entity = wide.parse_config_path(version_str, entity_path)
                if config_entity:
                    yield config_entity
                else:
                    template_entity = wide.parse_template_path(version_str, entity_path)
                    if template_entity:
                        yield template_entity

    def _get_active_version(self, activity: str) -> int:
        assert activity in SUPPORTED_ACTIVITIES
        version_file = os.path.join(self.config.base_path, activity, 'latest-version.json')
        if os.path.isfile(version_file):
            with open(version_file, 'r') as f:
                contents = json.load(f)
            if isinstance(contents, dict) and 'version' in contents and isinstance(contents['version'], int):
                version = contents['version']
                version_dir = os.path.join(self.config.base_path, activity, str(version))
                if os.path.isdir(version_dir):
                    return version
        return -1

    def _write_active_version(self, activity: str, version: int) -> None:
        activity_dir = os.path.join(self.config.base_path, activity)
        os.makedirs(activity_dir, exist_ok=True)
        version_file = os.path.join(activity_dir, 'latest-version.json')
        with open(version_file, 'w') as f:
            json.dump({'version': version}, f)

    @staticmethod
    def _parse_version(version: str) -> Tuple[str, int]:
        if '-' not in version:
            raise ValueError('invalid version number {0}'.format(version))
        pos = version.rindex('-')
        activity = version[0:pos]
        version_num = int(version[pos + 1:])
        return activity, version_num

    def _get_path(self, parts: List[str]) -> str:
        return os.path.join(self.config.base_path, *parts)

    def _split_path(self, full_path: str) -> List[str]:
        ret = []
        if not full_path.startswith(self.config.base_path):
            return ret
        current = full_path[len(self.config.base_path):]
        while True:
            rest, part = os.path.split(current)
            if part:
                ret.insert(0, part)
            if not rest:
                return ret
            current = rest
