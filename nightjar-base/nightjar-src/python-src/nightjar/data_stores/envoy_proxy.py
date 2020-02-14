
from typing import Iterable, Tuple, Optional
from .abc_backend import (
    AbcDataStoreBackend,
    ACTIVITY_PROXY_CONFIGURATION,
)


class EnvoyProxyDataStore:
    """
    API used by the envoy proxy servers for updating the envoy proxy configuration.
    """
    __version: Optional[str]

    def __init__(self, backend: AbcDataStoreBackend) -> None:
        self.__version = None
        self.backend = backend

    def __enter__(self) -> 'EnvoyProxyDataStore':
        assert self.__version is None
        self.__version = self.backend.get_active_version(ACTIVITY_PROXY_CONFIGURATION)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        # No special exit requirements
        self.__version = None

    def get_gateway_envoy_files(self, namespace_id: str, is_public: bool) -> Iterable[Tuple[str, Optional[str]]]:
        """
        Returns the list of (purpose, contents) for the dynamic envoy files of the namespace.
        If the bootstrap template requires a key and there is no
        content, then it must be returned with None data.
        """
        assert self.__version is not None
        for entity in self.backend.get_gateway_config_entities(
                self.__version, namespace=namespace_id, is_public=is_public
        ):
            yield entity.purpose, self.backend.download(self.__version, entity)

    def get_service_envoy_files(self, service_id: str) -> Iterable[Tuple[str, Optional[str]]]:
        """
        Returns the list of (purpose, contents) for the dynamic envoy files of the service/color.
        If the bootstrap template requires a key and there is no
        content, then it must be returned with None data.
        """
        assert self.__version is not None
        for entity in self.backend.get_service_id_config_entities(self.__version, service_id=service_id):
            yield entity.purpose, self.backend.download(self.__version, entity)
