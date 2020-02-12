
from typing import Iterable, Optional
from .abc_backend import (
    AbcDataStoreBackend,
    ServiceColorEntity,
    NamespaceEntity,
    ACTIVITY_TEMPLATE_DEFINITION,
)


class ManagerReadDataStore:
    """
    API used by tools that need to read the envoy templates used to construct the envoy files.

    TODO should this be replaced with the CollectorDataStore?
    """
    def __init__(self, backend: AbcDataStoreBackend, version: Optional[str] = None) -> None:
        self.__version = version or backend.get_active_version(ACTIVITY_TEMPLATE_DEFINITION)
        self.backend = backend

    def get_service_color_template(
            self,
            service: Optional[str], color: Optional[str],
            purpose: str,
    ) -> Optional[str]:
        for entity in self.backend.get_service_color_entities(
                version=self.__version,
                service=service,
                color=color,
                purpose=purpose,
                is_template=True
        ):
            return self.backend.download(version=self.__version, entity=entity)
        # Not found
        return None

    def get_namespace_template(
            self,
            namespace: Optional[str],
            purpose: str,
    ) -> Optional[str]:
        for entity in self.backend.get_namespace_entities(
                version=self.__version,
                namespace=namespace,
                purpose=purpose,
                is_template=True
        ):
            return self.backend.download(version=self.__version, entity=entity)
        # Not found
        return None

    def get_service_color_templates(self) -> Iterable[ServiceColorEntity]:
        return self.backend.get_service_color_entities(version=self.__version, is_template=True)

    def get_namespace_templates(self) -> Iterable[NamespaceEntity]:
        return self.backend.get_namespace_entities(version=self.__version, is_template=True)


class ManagerDataStore:
    """
    API used by tools that need to read and write the envoy templates used to construct the envoy files.
    """
    __version: Optional[str]

    def __init__(self, backend: AbcDataStoreBackend) -> None:
        self.__version = None
        self.backend = backend

    def __enter__(self) -> 'ManagerDataStore':
        assert self.__version is None
        self.__version = self.backend.start_changes(ACTIVITY_TEMPLATE_DEFINITION)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        if exc_val:
            # An error happened
            if self.__version:
                self.backend.rollback_changes(self.__version)
        elif self.__version:
            self.backend.commit_changes(self.__version)
        self.__version = None

    def set_service_color_template(
            self,
            service: Optional[str], color: Optional[str],
            purpose: str, contents: str,
    ) -> None:
        """
        Writes the template for the given key associated with the service/color.  The translation logic
        should interpret the optional service and key as:
            Request for service+color must have a template.  If the data store contains an exact match for
            service+color, use that.  Then if the data store contains an exact match for service but None color,
            use that.  Otherwise, use the None service/None color.
        If service is None, then color must be None.  This does not support a generic per-color template.
        """
        if not service and color:
            raise ValueError('To specify color, the service must also be specified.')
        assert self.__version is not None
        self.backend.upload(self.__version, ServiceColorEntity(service, color, purpose, True), contents)

    def set_namespace_template(
            self,
            namespace: Optional[str],
            purpose: str, contents: str,
    ) -> None:
        assert self.__version is not None
        self.backend.upload(self.__version, NamespaceEntity(namespace, purpose, True), contents)
