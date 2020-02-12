
from typing import Iterable, Optional
from .abc_backend import (
    AbcDataStoreBackend,
    Entity,
    NamespaceEntity,
    ServiceColorEntity,
    ACTIVITY_PROXY_CONFIGURATION,
)


class ConfigurationReaderDataStore:
    """
    API used by tools that need to read the previously generated configuration,
    so that it can be compared against the current configuration.
    """
    __version: Optional[str]

    def __init__(self, backend: AbcDataStoreBackend) -> None:
        self.__version = None
        self.backend = backend

    def __enter__(self) -> 'ConfigurationReaderDataStore':
        assert self.__version is None
        self.__version = self.backend.get_active_version(ACTIVITY_PROXY_CONFIGURATION)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        # Because this is read-only access, there is no special rollback or commit behavior.
        self.__version = None

    def list_service_color_entities(self) -> Iterable[ServiceColorEntity]:
        """Find all service/color content (non-template) entities for the currently active version."""
        assert self.__version is not None
        return self.backend.get_service_color_entities(self.__version, None, None, None, False)

    def list_namespace_entities(self) -> Iterable[NamespaceEntity]:
        """
        Find all the namespace content (non-template) entities for the currently active version.
        """
        assert self.__version is not None
        return self.backend.get_namespace_entities(self.__version, None, None, False)

    def download_entity_content(self, entity: Entity) -> Optional[str]:
        assert self.__version is not None
        return self.backend.download(self.__version, entity)


class ConfigurationWriterDataStore:
    """
    API used by tools that need to write the configured envoy templates.

    The general operation is:
        1. Perform updates to the backend.
        1. Commit the changes to the backend.
    """
    __version: Optional[str]

    def __init__(self, backend: AbcDataStoreBackend) -> None:
        self.__version = None
        self.backend = backend

    def __enter__(self) -> 'ConfigurationWriterDataStore':
        assert self.__version is None
        self.__version = self.backend.start_changes(ACTIVITY_PROXY_CONFIGURATION)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        if exc_val:
            # An error occurred.
            if self.__version:
                self.backend.rollback_changes(self.__version)
        elif self.__version:
            self.backend.commit_changes(self.__version)
        self.__version = None

    def no_change(self) -> None:
        """
        Marks this current write action as not changed.  All further attempts to write will fail.
        """
        assert self.__version is not None
        self.backend.rollback_changes(self.__version)
        self.__version = None

    def set_service_color_purpose_contents(self, service: str, color: str, purpose: str, contents: str) -> None:
        """
        The service/color purpose's file contents.

        This is a non-template file, used directly by the
        envoy proxy servers.  Because this is exact, the service and color cannot be None (only templates
        can use that).
        """
        assert self.__version is not None
        self.backend.upload(self.__version, ServiceColorEntity(service, color, purpose, False), contents)

    def set_namespace_purpose_contents(self, namespace: str, purpose: str, contents: str) -> None:
        """
        The namespace's purpose's file contents.

        This is a non-template file, used directly by the
        envoy proxy servers.  Because this is exact, the service and color cannot be None (only templates
        can use that).
        """
        assert self.__version is not None
        self.backend.upload(self.__version, NamespaceEntity(namespace, purpose, False), contents)

    def set_entity_contents(self, entity: Entity, contents: str) -> None:
        """
        Set an entity's file contents.  The entity must not be a template.
        """
        assert entity.is_template is False
        assert self.__version is not None
        self.backend.upload(self.__version, entity, contents)
