from typing import Dict, Optional, Iterable

from ..abc_backend import (
    AbcDataStoreBackend,
    ServiceColorEntity, NamespaceEntity, Entity
)


class MockBackend(AbcDataStoreBackend):
    active_version: Optional[str]
    namespace_entities: Dict[NamespaceEntity, str]
    service_color_entities: Dict[ServiceColorEntity, str]
    committed: Optional[str]

    def __init__(self):
        self.active_version = None
        self.namespace_entities = {}
        self.service_color_entities = {}
        self.committed = None

    def get_active_version(self, activity: str) -> str:
        assert self.active_version is None
        self.active_version = activity
        return activity

    def start_changes(self, activity: str) -> str:
        assert self.active_version is None
        self.active_version = activity
        return activity

    def commit_changes(self, version: str) -> None:
        assert self.active_version == version
        self.committed = version

    def download(self, version: str, entity: Entity) -> str:
        assert self.active_version == version
        if isinstance(entity, ServiceColorEntity):
            return self.service_color_entities[entity]
        assert isinstance(entity, NamespaceEntity)
        return self.namespace_entities[entity]

    def upload(self, version: str, entity: Entity, contents: str) -> None:
        assert self.active_version == version
        if isinstance(entity, ServiceColorEntity):
            self.service_color_entities[entity] = contents
        assert isinstance(entity, NamespaceEntity)
        self.namespace_entities[entity] = contents

    def get_namespace_entities(
            self, version: str, namespace: Optional[str] = None, purpose: Optional[str] = None,
            is_template: Optional[bool] = None
    ) -> Iterable[NamespaceEntity]:
        assert version == self.active_version
        for key in self.namespace_entities:
            if (
                    (namespace is None or key.namespace == namespace)
                    and (purpose is None or key.purpose == purpose)
                    and (is_template is None or key.is_template == is_template)
            ):
                yield key

    def get_service_color_entities(
            self, version: str, service: Optional[str] = None, color: Optional[str] = None,
            purpose: Optional[str] = None, is_template: Optional[bool] = None
    ) -> Iterable[ServiceColorEntity]:
        assert version == self.active_version
        assert not (service is not None and color is None)
        for key in self.service_color_entities:
            if (
                    (service is None or key.service == service)
                    and (color is None or key.color == color)
                    and (purpose is None or key.purpose == purpose)
                    and (is_template is None or key.is_template == is_template)
            ):
                yield key
