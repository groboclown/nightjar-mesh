
from typing import Iterable, Optional
from .abc_backend import (
    AbcDataStoreBackend,
    ConfigEntity,
    TemplateEntity,
    NamespaceTemplateEntity,
    as_namespace_template_entity,
    ServiceColorTemplateEntity,
    as_service_color_template_entity,
    GatewayConfigEntity,
    ServiceIdConfigEntity,
    ACTIVITY_TEMPLATE_DEFINITION,
    ACTIVITY_PROXY_CONFIGURATION,
)
from ....protect import RouteProtection


class ManagerReadDataStore:
    """
    API used by tools that need to read the envoy templates used to construct the envoy files.
    """
    __template_version: Optional[str]
    __config_version: Optional[str]

    def __init__(
            self,
            backend: AbcDataStoreBackend,
            template_version: Optional[str] = None,
            config_version: Optional[str] = None,
    ) -> None:
        self.__template_version = template_version
        self.__fixed_template_version = template_version is not None
        self.__config_version = config_version
        self.__fixed_config_version = config_version is not None
        self.backend = backend

    # For consistency in the API, this also has an enter/exit.
    def __enter__(self) -> 'ManagerReadDataStore':
        if (
                (not self.__fixed_config_version and self.__config_version)
                or (not self.__fixed_template_version and self.__template_version)
        ):
            raise RuntimeError("Already running inside a context.")
        if not self.__fixed_template_version:
            self.__template_version = self.backend.get_active_version(ACTIVITY_TEMPLATE_DEFINITION)
        if not self.__fixed_config_version:
            self.__config_version = self.backend.get_active_version(ACTIVITY_PROXY_CONFIGURATION)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        if not self.__fixed_template_version:
            self.__template_version = None
        if not self.__fixed_config_version:
            self.__config_version = None

    def get_template(self, entity: TemplateEntity) -> Optional[str]:
        assert self.__template_version
        return self.backend.download(version=self.__template_version, entity=entity)

    def get_generated_file(self, entity: ConfigEntity) -> Optional[str]:
        assert self.__config_version
        return self.backend.download(version=self.__config_version, entity=entity)

    def get_service_color_templates(self) -> Iterable[ServiceColorTemplateEntity]:
        assert self.__template_version
        return self.backend.get_service_color_template_entities(version=self.__template_version)

    def get_namespace_templates(self) -> Iterable[NamespaceTemplateEntity]:
        assert self.__template_version
        return self.backend.get_namespace_template_entities(version=self.__template_version)

    def get_generated_files(self) -> Iterable[ConfigEntity]:
        assert self.__config_version
        return self.backend.get_config_entities(version=self.__config_version)

    def get_service_id_generated_files(self) -> Iterable[ServiceIdConfigEntity]:
        assert self.__config_version
        return self.backend.get_service_id_config_entities(version=self.__config_version)

    def get_gateway_generated_files(self) -> Iterable[GatewayConfigEntity]:
        assert self.__config_version
        return self.backend.get_gateway_config_entities(version=self.__config_version)


class ManagerWriteDataStore:
    """
    API used by tools that need to read and write the envoy templates used to construct the envoy files.
    """
    __version: Optional[str]

    def __init__(self, backend: AbcDataStoreBackend) -> None:
        self.__version = None
        self.backend = backend

    def __enter__(self) -> 'ManagerWriteDataStore':
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

    def set_template(self, entity: TemplateEntity, contents: str) -> None:
        ns = as_namespace_template_entity(entity)
        if ns:
            self.set_namespace_template(ns.namespace, ns.protection, ns.purpose, contents)
            return
        sc = as_service_color_template_entity(entity)
        assert sc
        self.set_service_color_template(sc.namespace, sc.service, sc.color, sc.purpose, contents)

    def set_service_color_template(
            self,
            namespace_id: Optional[str], service: Optional[str], color: Optional[str],
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
        self.backend.upload(
            self.__version,
            ServiceColorTemplateEntity(namespace_id, service, color, purpose),
            contents
        )

    def set_namespace_template(
            self,
            namespace: Optional[str],
            protection: Optional[RouteProtection],
            purpose: str, contents: str,
    ) -> None:
        assert self.__version is not None
        self.backend.upload(
            self.__version,
            NamespaceTemplateEntity(namespace, protection, purpose),
            contents
        )
