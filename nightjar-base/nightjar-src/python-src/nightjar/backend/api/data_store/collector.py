
"""
Collector Data Store API definitions and data structures.
"""

from typing import Iterable, Tuple, Dict, Optional, Any

from .abc_backend import (
    AbcDataStoreBackend,
    NamespaceTemplateEntity,
    ServiceColorTemplateEntity,
    ACTIVITY_TEMPLATE_DEFINITION,
)
from ....msg import debug
from ....protect import RouteProtection


class MatchedNamespaceTemplate:
    """A namespace template match"""
    __slots__ = ('namespace_id', 'protection', 'purpose', 'source',)

    def __init__(
            self, namespace_id: str, protection: RouteProtection,
            source: NamespaceTemplateEntity,
    ) -> None:
        self.namespace_id = namespace_id
        self.purpose = source.purpose
        self.protection = protection
        self.source = source


class MatchedServiceColorTemplate:
    """A service/color template match."""
    __slots__ = ('namespace_id', 'service_id', 'service', 'color', 'purpose', 'source',)

    def __init__(
            self, namespace_id: str, service_id: str, service: str, color: str,
            source: ServiceColorTemplateEntity,
    ) -> None:
        self.namespace_id = namespace_id
        self.service_id = service_id
        self.service = service
        self.color = color
        self.purpose = source.purpose
        self.source = source

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MatchedServiceColorTemplate):
            return False
        return (
            self.namespace_id == other.namespace_id
            and self.service_id == other.service_id
            and self.service == other.service
            and self.color == other.color
            and self.purpose == other.purpose
            and self.source == other.source
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
            hash(self.namespace_id) + hash(self.service_id) + hash(self.service) +
            hash(self.color) + hash(self.purpose) + hash(self.source)
        )


class CollectorDataStore:
    """
    API used by the collectors, which read the AWS service information and transform that with the
    configuration to create files used by the envoy proxy.

    This may be combined with the configuration implementation.
    The collector just gathers the files.
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

    def get_namespace_templates(
            self, namespaces: Iterable[Tuple[str, RouteProtection]]
    ) -> Iterable[Tuple[MatchedNamespaceTemplate, str]]:
        """
        namespaces: list of the tuple (namespace_id, protection).

        Returns the namespace templates registered in the system and the contents.
        """
        assert self.__version is not None
        entities = list(self.backend.get_namespace_template_entities(self.__version))
        debug("loaded version {v} entities: {e}", v=self.__version, e=entities)
        for namespace, protection in namespaces:
            purpose_matches: Dict[str, NamespaceTemplateEntity] = {}
            for entity in entities:
                existing = purpose_matches.get(entity.purpose)
                if (  # pylint: disable=R0916
                        # Priority 1: exact match, regardless of existing match
                        (entity.namespace == namespace and entity.protection == protection)

                        # Priority 2: namespace match, protection isn't.
                        or (
                            not existing
                            and entity.namespace == namespace
                            and entity.is_default_protection()
                        )
                        or (
                            existing
                            and existing.is_default_namespace()
                            and entity.namespace == namespace
                            and entity.is_default_protection()
                        )

                        # Priority 3: namespace default, protection match.
                        or (
                            not existing
                            and entity.is_default_namespace()
                            and entity.protection == protection
                        )
                        or (
                            existing
                            and existing.is_default_namespace()
                            and existing.is_default_protection()
                            and entity.is_default_namespace()
                            and entity.protection == protection
                        )

                        # Priority 4: defaults only if there is no existing match
                        or (
                            not existing
                            and entity.is_default_namespace()
                            and entity.is_default_protection()
                        )
                ):
                    purpose_matches[entity.purpose] = entity
            if not purpose_matches:
                raise ValueError(
                    'No match for namespace {0}, and there is no default'.format(namespace)
                )
            for value in purpose_matches.values():
                yield (
                    MatchedNamespaceTemplate(namespace, protection, value),
                    self.backend.download(self.__version, value)
                )

    def get_service_color_templates(
            self, namespace_service_colors: Iterable[Tuple[str, str, str, str]]
    ) -> Iterable[Tuple[MatchedServiceColorTemplate, str]]:
        """
        Each input is of the form namespace, service_id, service, color.

        Returns the service color templates registered in the system.  This is all the
        templates, including the envoy proxy backend.  For each item, it returns
            MatchedServiceColorTemplate, contents
        """
        assert self.__version is not None
        entities = list(self.backend.get_service_color_template_entities(self.__version))
        for namespace, service_id, service, color in namespace_service_colors:
            purpose_matches: Dict[str, Tuple[ServiceColorTemplateEntity, int]] = {}
            for entity in entities:
                _, existing_match_level = purpose_matches.get(entity.purpose, (None, 100,))

                if (
                        entity.namespace == namespace
                        and entity.service == service
                        and entity.color == color
                ):
                    # Match level 1: exact match on everything.  Doesn't matter about
                    # the current value.
                    purpose_matches[entity.purpose] = (entity, 1,)

                elif (
                        existing_match_level > 2
                        and entity.namespace == namespace
                        and entity.service == service
                        and entity.is_default_color()
                ):
                    # Priority 2: namespace match, service match, default color
                    purpose_matches[entity.purpose] = (entity, 2,)

                elif (
                        existing_match_level > 3
                        and entity.namespace == namespace
                        and entity.is_default_service()
                        and entity.is_default_color()
                ):
                    # Priority 3: namespace match, default service and color.
                    purpose_matches[entity.purpose] = (entity, 3,)

                elif (
                        existing_match_level > 4
                        and entity.is_default_namespace()
                        and entity.service == service
                        and entity.color == color
                ):
                    # Priority 4: service and color match, default namespace
                    purpose_matches[entity.purpose] = (entity, 4,)

                elif (
                        existing_match_level > 5
                        and entity.is_default_namespace()
                        and entity.service == service
                        and entity.is_default_color()
                ):
                    # Priority 5: service matches, namespace and color are default.
                    purpose_matches[entity.purpose] = (entity, 5,)

                elif (
                        existing_match_level > 6
                        and entity.is_default_namespace()
                        and entity.is_default_service()
                        and entity.color == color
                ):
                    # Priority 6: service and namespace are default, color is match.
                    purpose_matches[entity.purpose] = (entity, 6,)

                elif (
                        existing_match_level > 99
                        and entity.is_default_namespace()
                        and entity.is_default_service()
                        and entity.is_default_color()
                ):
                    # Final priority: default everything.
                    purpose_matches[entity.purpose] = (entity, 99,)

            if not purpose_matches:
                raise ValueError(
                    (
                        'No match for namespace {0} service {1}, '
                        'color {2}, and there is no default'
                    ).format(
                        namespace, service, color,
                    )
                )
            for value, _ in purpose_matches.values():
                yield (
                    MatchedServiceColorTemplate(namespace, service_id, service, color, value),
                    self.backend.download(self.__version, value),
                )
