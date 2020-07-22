
"""Mock handlers for the collector datastore backends."""

from typing import List, Dict, Set, Optional, Iterable

from .. import ConfigEntity
from ..abc_backend import (
    AbcDataStoreBackend,
    Entity,
    NamespaceTemplateEntity,
    as_namespace_template_entity,
    ServiceIdConfigEntity,
    as_service_id_config_entity,
    GatewayConfigEntity,
    as_gateway_config_entity,
    ServiceColorTemplateEntity,
    as_service_color_template_entity,
    TemplateEntity,
)
from .....protect import RouteProtection


class MockBackend(AbcDataStoreBackend):
    """Back-end data store mock object."""
    active_versions: Set[str]
    namespace_entities: Dict[NamespaceTemplateEntity, str]
    service_color_entities: Dict[ServiceColorTemplateEntity, str]
    gateway_entities: Dict[GatewayConfigEntity, str]
    service_id_entities: Dict[ServiceIdConfigEntity, str]
    committed: Optional[str]

    def __init__(self):
        self.active_versions = set()
        self.namespace_entities = {}
        self.service_color_entities = {}
        self.gateway_entities = {}
        self.service_id_entities = {}
        self.committed = None

    def get_active_version(self, activity: str) -> str:
        assert activity not in self.active_versions
        self.active_versions.add(activity)
        return activity

    def start_changes(self, activity: str) -> str:
        assert activity not in self.active_versions
        self.active_versions.add(activity)
        return activity

    def commit_changes(self, version: str) -> None:
        assert version in self.active_versions
        self.committed = version

    def download(self, version: str, entity: Entity) -> str:
        assert version in self.active_versions
        sct = as_service_color_template_entity(entity)
        if sct:
            return self.service_color_entities[sct]
        nte = as_namespace_template_entity(entity)
        if nte:
            return self.namespace_entities[nte]
        sic = as_service_id_config_entity(entity)
        if sic:
            return self.service_id_entities[sic]
        gwc = as_gateway_config_entity(entity)
        assert gwc
        return self.gateway_entities[gwc]

    def upload(self, version: str, entity: Entity, contents: str) -> None:
        assert version in self.active_versions
        sct = as_service_color_template_entity(entity)
        if sct:
            self.service_color_entities[sct] = contents
            return
        nte = as_namespace_template_entity(entity)
        if nte:
            self.namespace_entities[nte] = contents
            return
        sic = as_service_id_config_entity(entity)
        if sic:
            self.service_id_entities[sic] = contents
            return
        gwc = as_gateway_config_entity(entity)
        assert gwc
        self.gateway_entities[gwc] = contents

    def rollback_changes(self, version: str) -> None:
        self.active_versions.remove(version)
        self.gateway_entities = {}
        self.service_id_entities = {}
        self.service_color_entities = {}
        self.namespace_entities = {}

    def get_template_entities(self, version: str) -> Iterable[TemplateEntity]:
        ret: List[TemplateEntity] = list(self.service_color_entities.keys())
        ret.extend(self.namespace_entities.keys())
        return ret

    def get_config_entities(self, version: str) -> Iterable[ConfigEntity]:
        ret: List[ConfigEntity] = list(self.service_id_entities.keys())
        ret.extend(self.gateway_entities.keys())
        return ret

    def get_namespace_template_entities(
            self, version: str, namespace: Optional[str] = None,
            protection: Optional[RouteProtection] = None, purpose: Optional[str] = None,
    ) -> Iterable[NamespaceTemplateEntity]:
        for entity in self.namespace_entities:
            if (
                    (namespace is None or namespace == entity.namespace)
                    and (protection is None or protection == entity.protection)
                    and (purpose is None or purpose == entity.purpose)
            ):
                yield entity

    def get_gateway_config_entities(
            self, version: str, namespace: Optional[str] = None,
            protection: Optional[RouteProtection] = None, purpose: Optional[str] = None,
    ) -> Iterable[GatewayConfigEntity]:
        for entity in self.gateway_entities:
            if (
                    (namespace is None or namespace == entity.namespace_id)
                    and (protection is None or protection == entity.protection)
                    and (purpose is None or purpose == entity.purpose)
            ):
                yield entity

    def get_service_color_template_entities(
            self, version: str, namespace: Optional[str] = None,
            service: Optional[str] = None, color: Optional[str] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[ServiceColorTemplateEntity]:
        for entity in self.service_color_entities:
            if (
                    (namespace is None or namespace == entity.namespace)
                    and (service is None or service == entity.service)
                    and (color is None or color == entity.color)
                    and (purpose is None or purpose == entity.purpose)
            ):
                yield entity

    def get_service_id_config_entities(
            self, version: str, namespace_id: Optional[str] = None,
            service_id: Optional[str] = None, service: Optional[str] = None,
            color: Optional[str] = None, purpose: Optional[str] = None,
    ) -> Iterable[ServiceIdConfigEntity]:
        for entity in self.service_id_entities:
            if (
                    (namespace_id is None or namespace_id == entity.namespace_id)
                    and (service_id is None or service_id == entity.service_id)
                    and (service is None or service == entity.service)
                    and (color is None or color == entity.color)
                    and (purpose is None or purpose == entity.purpose)
            ):
                yield entity
