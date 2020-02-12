
from typing import Iterable, Tuple, Dict, Optional

from .abc_backend import (
    AbcDataStoreBackend,
    ServiceColorEntity,
    NamespaceEntity,
    ACTIVITY_TEMPLATE_DEFINITION,
)
from ..msg import debug


class CollectorDataStore:
    """
    API used by the collectors, which read the AWS service information and transform that with the
    configuration to create files used by the envoy proxy.

    This may be combined with the configuration implementation.  The collector just gathers the files.
    """
    __version: Optional[str]

    def __init__(self, backend: AbcDataStoreBackend) -> None:
        self.__version = None
        self.backend = backend

    def __enter__(self) -> 'CollectorDataStore':
        assert self.__version is None
        self.__version = self.backend.get_active_version(ACTIVITY_TEMPLATE_DEFINITION)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        # No special exit requirements.
        self.__version = None

    def get_service_color_templates(
            self, service_colors: Iterable[Tuple[str, str]]
    ) -> Iterable[Tuple[Tuple[str, str], str, str]]:
        """
        Returns the service color templates registered in the system.  This is all the
        templates, including the envoy proxy backend.  For each item, it returns
            (service, color), purpose, contents
        """
        assert self.__version is not None
        entities = list(self.backend.get_service_color_entities(self.__version, is_template=True))
        for service_color in service_colors:
            purpose_matches: Dict[str, ServiceColorEntity] = {}
            for entity in entities:
                existing = purpose_matches.get(entity.purpose)
                if (
                        # Priority 1: exact match.  Doesn't matter about the current value.
                        (entity.service == service_color[0] and entity.color == service_color[1])
                        # Priority 2: no existing match with service name match and default color.
                        or (not existing and entity.service == service_color[0] and entity.is_default_color())
                        # Priority 3: service name match and default color and current service is default.
                        or (
                            existing
                            and existing.is_default_service()
                            and entity.service == service_color[0]
                            and entity.is_default_color()
                        )
                        # Priority 4: no existing match and default match
                        or (not existing and entity.is_default_service() and entity.is_default_color())
                ):
                    purpose_matches[entity.purpose] = entity
            if not purpose_matches:
                raise ValueError(
                    'No match for service {0}, color {1}, and there is no default'.format(
                        service_color[0], service_color[1]
                    )
                )
            for value in purpose_matches.values():
                yield service_color, value.purpose, self.backend.download(self.__version, value)

    def get_namespace_templates(
            self, namespaces: Iterable[str]
    ) -> Iterable[Tuple[str, str, str]]:
        """
        Returns the namespace templates registered in the system.  Each item is the namespace, purpose, contents.
        """
        assert self.__version is not None
        entities = list(self.backend.get_namespace_entities(self.__version, is_template=True))
        debug("loaded version {v} entities: {e}", v=self.__version, e=entities)
        for namespace in namespaces:
            purpose_matches: Dict[str, NamespaceEntity] = {}
            for entity in entities:
                existing = purpose_matches.get(entity.purpose)
                if (
                        # Priority 1: exact match, regardless of existing match
                        entity.namespace == namespace
                        # Priority 2: default namespace only if there is no existing match
                        or (not existing and entity.is_default_namespace())
                ):
                    purpose_matches[entity.purpose] = entity
            if not purpose_matches:
                raise ValueError('No match for namespace {0}, and there is no default'.format(namespace))
            for value in purpose_matches.values():
                yield namespace, value.purpose, self.backend.download(self.__version, value)
