
from .abc_backend import (
    AbcDataStoreBackend,
    ServiceColorEntity,
    NamespaceEntity,
    ACTIVITY_PROXY_CONFIGURATION,
)


class ConfigurationDataStore:
    """
    API used by tools that need to read and write the envoy templates used to construct the envoy files.

    The general operation is:
        1. Perform updates to the backend.
        1. Commit the changes to the backend.
    """
    def __init__(self, backend: AbcDataStoreBackend) -> None:
        self.__active = True
        self.__version = backend.start_changes(ACTIVITY_PROXY_CONFIGURATION)
        self.backend = backend

    def commit(self) -> None:
        self._assert_active()
        self.__active = False
        self.backend.commit_changes(self.__version)

    def set_service_color_purpose_contents(self, service: str, color: str, purpose: str, contents: str) -> None:
        """
        The service/color purpose file's contents.

        This is a non-template file, used directly by the
        envoy proxy servers.  Because this is exact, the service and color cannot be None (only templates
        can use that).
        """
        self._assert_active()
        self.backend.upload(self.__version, ServiceColorEntity(service, color, purpose, False), contents)

    def set_namespace_purpose_contents(self, namespace: str, purpose: str, contents: str) -> None:
        """
        The namespace's purpose file's contents.

        This is a non-template file, used directly by the
        envoy proxy servers.  Because this is exact, the service and color cannot be None (only templates
        can use that).
        """
        self._assert_active()
        self.backend.upload(self.__version, NamespaceEntity(namespace, purpose, False), contents)

    def _assert_active(self) -> None:
        if not self.__active:
            raise RuntimeError('Executed action on closed store')
