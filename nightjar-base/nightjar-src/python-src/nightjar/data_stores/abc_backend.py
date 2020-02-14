

"""
Standard Prototype that the data stores must implement.
"""

from typing import Iterable, Optional, Union, Any
import abc

ACTIVITY_PROXY_CONFIGURATION = 'proxy-configuration'
ACTIVITY_TEMPLATE_DEFINITION = 'template-creation'
SUPPORTED_ACTIVITIES = (
    ACTIVITY_PROXY_CONFIGURATION,
    ACTIVITY_TEMPLATE_DEFINITION,
)


class BaseEntity:
    __slots__ = ('__activity', '__purpose')

    def __init__(self, activity: str, purpose: str) -> None:
        self.__activity = activity
        self.__purpose = purpose

    @property
    def activity(self) -> str:
        return self.__activity

    @property
    def purpose(self) -> str:
        return self.__purpose


class NamespaceTemplateEntity(BaseEntity):
    """
    Describes a namespace-based entity in the ACTIVITY_TEMPLATE_DEFINITION activity,
    which can optionally be the default namespace.
    """
    __slots__ = ('__namespace', '__is_public')

    def __init__(self, namespace: Optional[str], is_public: Optional[bool], purpose: str) -> None:
        BaseEntity.__init__(self, ACTIVITY_TEMPLATE_DEFINITION, purpose)
        self.__namespace = namespace
        self.__is_public = is_public

    @property
    def namespace(self) -> Optional[str]:
        return self.__namespace

    def is_default_namespace(self) -> bool:
        return self.namespace is None

    @property
    def is_public(self) -> Optional[bool]:
        return self.__is_public

    def is_default_public(self) -> bool:
        return self.__is_public is None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NamespaceTemplateEntity):
            return False
        return (
            self.__namespace == other.__namespace
            and self.__is_public == other.__is_public
            and self.purpose == other.purpose
            and self.activity == other.activity
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.__namespace) + hash(self.__is_public) + hash(self.purpose) + hash(self.activity)

    def __repr__(self) -> str:
        return (
            'NamespaceTemplateEntity(namespace={namespace}, is_public={is_public}, activity={activity}, '
            'purpose={purpose})'
        ).format(
            namespace=repr(self.__namespace),
            is_public=repr(self.__is_public),
            activity=repr(self.activity),
            purpose=repr(self.purpose),
        )


class GatewayConfigEntity(BaseEntity):
    """
    Describes a namespace-based entity in the ACTIVITY_TEMPLATE_DEFINITION activity,
    which can optionally be the default namespace.
    """
    __slots__ = ('__namespace_id', '__is_public',)

    def __init__(self, namespace_id: str, is_public: bool, purpose: str) -> None:
        BaseEntity.__init__(self, ACTIVITY_PROXY_CONFIGURATION, purpose)
        self.__namespace_id = namespace_id
        self.__is_public = is_public

    @property
    def namespace_id(self) -> str:
        return self.__namespace_id

    @property
    def is_public(self) -> bool:
        return self.__is_public

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, GatewayConfigEntity):
            return False
        return (
            self.__namespace_id == other.__namespace_id
            and self.__is_public == other.__is_public
            and self.purpose == other.purpose
            and self.activity == other.activity
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.__namespace_id) + hash(self.__is_public) + hash(self.purpose) + hash(self.activity)

    def __repr__(self) -> str:
        return (
            'GatewayConfigEntity(namespace_id={namespace_id}, is_public={is_public}, activity={activity}, '
            'purpose={purpose})'
        ).format(
            namespace_id=repr(self.__namespace_id),
            is_public=repr(self.__is_public),
            activity=repr(self.activity),
            purpose=repr(self.purpose),
        )


class ServiceColorTemplateEntity(BaseEntity):
    __slots__ = ('__namespace', '__service', '__color',)

    def __init__(
            self, namespace: Optional[str], service: Optional[str], color: Optional[str], purpose: str
    ) -> None:
        BaseEntity.__init__(self, ACTIVITY_TEMPLATE_DEFINITION, purpose)
        self.__namespace = namespace
        self.__service = service
        self.__color = color

    @property
    def namespace(self) -> Optional[str]:
        return self.__namespace

    def is_default_namespace(self) -> bool:
        return self.namespace is None

    @property
    def service(self) -> Optional[str]:
        return self.__service

    def is_default_service(self) -> bool:
        return self.__service is None

    @property
    def color(self) -> Optional[str]:
        return self.__color

    def is_default_color(self) -> bool:
        return self.__color is None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ServiceColorTemplateEntity):
            return False
        return (
                self.__namespace == other.__namespace
                and self.__service == other.__service
                and self.__color == other.__color
                and self.purpose == other.purpose
                and self.activity == other.activity
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
                hash(self.__namespace) + hash(self.__service) + hash(self.__color) +
                hash(self.purpose) + hash(self.activity)
        )

    def __repr__(self) -> str:
        return (
            'ServiceColorTemplateEntity(namespace={namespace}, service={service}, color={color}, '
            'purpose={purpose}, activity={activity})'
        ).format(
            namespace=repr(self.__namespace),
            service=repr(self.__service),
            color=repr(self.__color),
            purpose=repr(self.purpose),
            activity=repr(self.activity),
        )


class ServiceIdConfigEntity(BaseEntity):
    __slots__ = ('__namespace_id', '__service_id', '__service', '__color',)

    def __init__(
            self, namespace_id: str, service_id: str, service: str, color: str, purpose: str
    ) -> None:
        BaseEntity.__init__(self, ACTIVITY_PROXY_CONFIGURATION, purpose)
        self.__namespace_id = namespace_id
        self.__service_id = service_id
        self.__service = service
        self.__color = color

    @property
    def namespace_id(self) -> str:
        return self.__namespace_id

    @property
    def service_id(self) -> str:
        return self.__service_id

    @property
    def service(self) -> str:
        return self.__service

    @property
    def color(self) -> str:
        return self.__color

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ServiceIdConfigEntity):
            return False
        return (
                self.__namespace_id == other.__namespace_id
                and self.__service_id == other.__service_id
                and self.__service == other.__service
                and self.__color == other.__color
                and self.purpose == other.purpose
                and self.activity == other.activity
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
                hash(self.__service_id) + hash(self.__service) + hash(self.__color) +
                hash(self.purpose) + hash(self.activity)
        )

    def __repr__(self) -> str:
        return (
            'ServiceIdConfigEntity(service_id={service_id}, service={service}, color={color}, '
            'purpose={purpose}, activity={activity})'
        ).format(
            service_id=repr(self.__service_id),
            service=repr(self.__service),
            color=repr(self.__color),
            purpose=repr(self.purpose),
            activity=repr(self.activity),
        )


Entity = Union[NamespaceTemplateEntity, GatewayConfigEntity, ServiceColorTemplateEntity, ServiceIdConfigEntity]
TemplateEntity = Union[NamespaceTemplateEntity, ServiceColorTemplateEntity]
ConfigEntity = Union[GatewayConfigEntity, ServiceIdConfigEntity]


def as_template_entity(entity: Entity) -> Optional[TemplateEntity]:
    if isinstance(entity, (NamespaceTemplateEntity, ServiceColorTemplateEntity)):
        return entity
    return None


def as_config_entity(entity: Entity) -> Optional[ConfigEntity]:
    if isinstance(entity, (GatewayConfigEntity, ServiceIdConfigEntity)):
        return entity
    return None


def as_namespace_template_entity(entity: Entity) -> Optional[NamespaceTemplateEntity]:
    if isinstance(entity, NamespaceTemplateEntity):
        return entity
    return None


def as_gateway_config_entity(entity: Entity) -> Optional[GatewayConfigEntity]:
    if isinstance(entity, GatewayConfigEntity):
        return entity
    return None


def as_service_color_template_entity(entity: Entity) -> Optional[ServiceColorTemplateEntity]:
    if isinstance(entity, ServiceColorTemplateEntity):
        return entity
    return None


def as_service_id_config_entity(entity: Entity) -> Optional[ServiceIdConfigEntity]:
    if isinstance(entity, ServiceIdConfigEntity):
        return entity
    return None


class AbcDataStoreBackend(abc.ABC):
    """
    API used by the collectors, which read the AWS service information and transform that with the
    configuration to create files used by the envoy proxy.
    """

    def get_active_version(self, activity: str) -> str:
        """
        Discover the most recent completed version.  This always begins a series of atomic actions.
        The backend should maintain a certain number of these, based on time.
        """
        raise NotImplementedError()

    def start_changes(self, activity: str) -> str:
        """
        Tells the backend that changes to the data store are starting.  The data assigns
        these changes to a version string.
        """
        raise NotImplementedError()

    def commit_changes(self, version: str) -> None:
        """
        All the changes that have been made need to be committed, so that any active process
        that's pulling doesn't get a mix of old and new configurations.  This commit process
        can also clean up old data.
        """
        raise NotImplementedError()

    def rollback_changes(self, version: str) -> None:
        """Performed on error, to revert any uploads."""
        raise NotImplementedError()

    def download(self, version: str, entity: Entity) -> str:
        """Download the contents of the entry."""
        raise NotImplementedError()

    def upload(self, version: str, entity: Entity, contents: str) -> None:
        """Upload the given entry key with the given contents."""
        raise NotImplementedError()

    def get_template_entities(self, version: str) -> Iterable[TemplateEntity]:
        """
        Returns all template entities stored for the given version.  This can
        potentially conserve on API calls.
        """
        raise NotImplementedError()

    def get_config_entities(self, version: str) -> Iterable[ConfigEntity]:
        """
        Returns all configuration entities stored for the given version.  This can
        potentially conserve on API calls.
        """
        raise NotImplementedError()

    def get_namespace_template_entities(
            self,
            version: str,
            namespace: Optional[str] = None,
            is_public: Optional[bool] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[NamespaceTemplateEntity]:
        """
        Get the entities that match the namespace and purpose.  If either is None, then it acts as a
        wild-card.
        """
        raise NotImplementedError()

    def get_gateway_config_entities(
            self,
            version: str,
            namespace: Optional[str] = None,
            is_public: Optional[bool] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[GatewayConfigEntity]:
        """
        Get the entities for the by-namespace templates.

        If namespace or purpose are None, then they act as wildcards.
        """
        raise NotImplementedError()

    def get_service_color_template_entities(
            self,
            version: str,
            namespace: Optional[str] = None,
            service: Optional[str] = None,
            color: Optional[str] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[ServiceColorTemplateEntity]:
        """
        Get the entities for the by-service/color templates.

        If any argument is None, then it acts as a wildcard.
        """
        raise NotImplementedError()

    def get_service_id_config_entities(
            self,
            version: str,
            namespace_id: Optional[str] = None,
            service_id: Optional[str] = None,
            service: Optional[str] = None,
            color: Optional[str] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[ServiceIdConfigEntity]:
        """
        Get the entities for the by-service configurations.

        If any argument is None, then it acts as a wildcard.
        """
        raise NotImplementedError()
