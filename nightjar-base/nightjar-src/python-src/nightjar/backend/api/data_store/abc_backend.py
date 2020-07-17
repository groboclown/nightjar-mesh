

"""
Standard Prototype that the data stores must implement.
"""

from typing import Iterable, Optional, Union, Any
import abc
from ....protect import RouteProtection

ACTIVITY_PROXY_CONFIGURATION = 'proxy-configuration'
ACTIVITY_TEMPLATE_DEFINITION = 'template-creation'
SUPPORTED_ACTIVITIES = (
    ACTIVITY_PROXY_CONFIGURATION,
    ACTIVITY_TEMPLATE_DEFINITION,
)


class BaseEntity:
    """Base class for entity types."""
    __slots__ = ('__activity', '__purpose')

    def __init__(self, activity: str, purpose: str) -> None:
        self.__activity = activity
        self.__purpose = purpose

    @property
    def activity(self) -> str:
        """The kind of activity the entity is associated with."""
        return self.__activity

    @property
    def purpose(self) -> str:
        """The prupose of the entity."""
        return self.__purpose


class NamespaceTemplateEntity(BaseEntity):
    """
    Describes a namespace-based entity in the ACTIVITY_TEMPLATE_DEFINITION activity,
    which can optionally be the default namespace.
    """
    __slots__ = ('__namespace', '__protection')

    def __init__(
            self,
            namespace: Optional[str],
            protection: Optional[RouteProtection], purpose: str,
    ) -> None:
        BaseEntity.__init__(self, ACTIVITY_TEMPLATE_DEFINITION, purpose)
        self.__namespace = namespace
        self.__protection = protection

    @property
    def namespace(self) -> Optional[str]:
        """Namespace for this entity.  None means the default namespace."""
        return self.__namespace

    def is_default_namespace(self) -> bool:
        """Is this the default namespace?"""
        return self.namespace is None

    @property
    def protection(self) -> Optional[RouteProtection]:
        """Protection for this namespace. None means default protection level."""
        return self.__protection

    def is_default_protection(self) -> bool:
        """Is this the default protection level?"""
        return self.__protection is None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NamespaceTemplateEntity):
            return False
        return (
            self.__namespace == other.namespace
            and self.__protection == other.protection
            and self.purpose == other.purpose
            and self.activity == other.activity
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
            hash(self.__namespace) +
            hash(self.__protection) +
            hash(self.purpose) +
            hash(self.activity)
        )

    def __repr__(self) -> str:
        return (
            'NamespaceTemplateEntity(namespace={namespace}, protection={protection}, '
            'activity={activity}, purpose={purpose})'
        ).format(
            namespace=repr(self.__namespace),
            protection=repr(self.__protection),
            activity=repr(self.activity),
            purpose=repr(self.purpose),
        )


class GatewayConfigEntity(BaseEntity):
    """
    Describes a namespace-based entity in the ACTIVITY_TEMPLATE_DEFINITION activity,
    which can optionally be the default namespace.
    """
    __slots__ = ('__namespace_id', '__protection',)

    def __init__(self, namespace_id: str, protection: RouteProtection, purpose: str) -> None:
        BaseEntity.__init__(self, ACTIVITY_PROXY_CONFIGURATION, purpose)
        self.__namespace_id = namespace_id
        self.__protection = protection

    @property
    def namespace_id(self) -> str:
        """Opaque ID for this gateway's namespace."""
        return self.__namespace_id

    @property
    def protection(self) -> RouteProtection:
        """Protection level for the gateway."""
        return self.__protection

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, GatewayConfigEntity):
            return False
        return (
            self.__namespace_id == other.namespace_id
            and self.__protection == other.protection
            and self.purpose == other.purpose
            and self.activity == other.activity
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
            hash(self.__namespace_id) +
            hash(self.__protection) +
            hash(self.purpose) +
            hash(self.activity)
        )

    def __repr__(self) -> str:
        return (
            'GatewayConfigEntity(namespace_id={namespace_id}, protection={protection}, '
            'activity={activity}, purpose={purpose})'
        ).format(
            namespace_id=repr(self.__namespace_id),
            protection=repr(self.__protection),
            activity=repr(self.activity),
            purpose=repr(self.purpose),
        )


class ServiceColorTemplateEntity(BaseEntity):
    """Entity for service/color templates."""
    __slots__ = ('__namespace', '__service', '__color',)

    def __init__(
            self, namespace: Optional[str],
            service: Optional[str],
            color: Optional[str], purpose: str,
    ) -> None:
        BaseEntity.__init__(self, ACTIVITY_TEMPLATE_DEFINITION, purpose)
        self.__namespace = namespace
        self.__service = service
        self.__color = color

    @property
    def namespace(self) -> Optional[str]:
        """Namespace for the service/color."""
        return self.__namespace

    def is_default_namespace(self) -> bool:
        """Is this the default namespace?"""
        return self.namespace is None

    @property
    def service(self) -> Optional[str]:
        """Name for the service."""
        return self.__service

    def is_default_service(self) -> bool:
        """Is this the default service?"""
        return self.__service is None

    @property
    def color(self) -> Optional[str]:
        """Service color."""
        return self.__color

    def is_default_color(self) -> bool:
        """Is this the default service color?"""
        return self.__color is None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ServiceColorTemplateEntity):
            return False
        return (
            self.__namespace == other.namespace
            and self.__service == other.service
            and self.__color == other.color
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
    """Specific instance of a service."""
    __slots__ = ('__namespace_id', '__service_id', '__service', '__color',)

    def __init__(
            self, namespace_id: str, service_id: str, service: str, color: str, purpose: str,
    ) -> None:
        BaseEntity.__init__(self, ACTIVITY_PROXY_CONFIGURATION, purpose)
        self.__namespace_id = namespace_id
        self.__service_id = service_id
        self.__service = service
        self.__color = color

    @property
    def namespace_id(self) -> str:
        """Opaque namespace ID."""
        return self.__namespace_id

    @property
    def service_id(self) -> str:
        """Opaque service ID."""
        return self.__service_id

    @property
    def service(self) -> str:
        """Associated service."""
        return self.__service

    @property
    def color(self) -> str:
        """Associated color."""
        return self.__color

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ServiceIdConfigEntity):
            return False
        return (
            self.__namespace_id == other.namespace_id
            and self.__service_id == other.service_id
            and self.__service == other.service
            and self.__color == other.color
            and self.purpose == other.purpose
            and self.activity == other.activity
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
            hash(self.__namespace_id) +
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


Entity = Union[
    NamespaceTemplateEntity, GatewayConfigEntity,
    ServiceColorTemplateEntity, ServiceIdConfigEntity,
]
TemplateEntity = Union[NamespaceTemplateEntity, ServiceColorTemplateEntity]
ConfigEntity = Union[GatewayConfigEntity, ServiceIdConfigEntity]


def as_template_entity(entity: Entity) -> Optional[TemplateEntity]:
    """Converts this to a template style entity, or None if not one of them."""
    if isinstance(entity, (NamespaceTemplateEntity, ServiceColorTemplateEntity)):
        return entity
    return None


def as_config_entity(entity: Entity) -> Optional[ConfigEntity]:
    """Converts this to a config style entity, or None if not one of them."""
    if isinstance(entity, (GatewayConfigEntity, ServiceIdConfigEntity)):
        return entity
    return None


def as_namespace_template_entity(entity: Entity) -> Optional[NamespaceTemplateEntity]:
    """Converts this to a namespace template entity, or None if not one."""
    if isinstance(entity, NamespaceTemplateEntity):
        return entity
    return None


def as_gateway_config_entity(entity: Entity) -> Optional[GatewayConfigEntity]:
    """Converts this to a gateway config entity, or None if not one."""
    if isinstance(entity, GatewayConfigEntity):
        return entity
    return None


def as_service_color_template_entity(entity: Entity) -> Optional[ServiceColorTemplateEntity]:
    """Converts this to a service/color template entity, or None if not one."""
    if isinstance(entity, ServiceColorTemplateEntity):
        return entity
    return None


def as_service_id_config_entity(entity: Entity) -> Optional[ServiceIdConfigEntity]:
    """Converts this to a service ID configuration entity, or None if not one."""
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
        raise NotImplementedError()  # pragma no cover

    def start_changes(self, activity: str) -> str:
        """
        Tells the backend that changes to the data store are starting.  The data assigns
        these changes to a version string.
        """
        raise NotImplementedError()  # pragma no cover

    def commit_changes(self, version: str) -> None:
        """
        All the changes that have been made need to be committed, so that any active process
        that's pulling doesn't get a mix of old and new configurations.  This commit process
        can also clean up old data.
        """
        raise NotImplementedError()  # pragma no cover

    def rollback_changes(self, version: str) -> None:
        """Performed on error, to revert any uploads."""
        raise NotImplementedError()  # pragma no cover

    def download(self, version: str, entity: Entity) -> str:
        """Download the contents of the entry."""
        raise NotImplementedError()  # pragma no cover

    def upload(self, version: str, entity: Entity, contents: str) -> None:
        """Upload the given entry key with the given contents."""
        raise NotImplementedError()  # pragma no cover

    def get_template_entities(self, version: str) -> Iterable[TemplateEntity]:
        """
        Returns all template entities stored for the given version.  This can
        potentially conserve on API calls.
        """
        raise NotImplementedError()  # pragma no cover

    def get_config_entities(self, version: str) -> Iterable[ConfigEntity]:
        """
        Returns all configuration entities stored for the given version.  This can
        potentially conserve on API calls.
        """
        raise NotImplementedError()  # pragma no cover

    def get_namespace_template_entities(
            self,
            version: str,
            namespace: Optional[str] = None,
            protection: Optional[RouteProtection] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[NamespaceTemplateEntity]:
        """
        Get the entities that match the namespace and purpose.  If either is None, then it acts
        as a wild-card.
        """
        raise NotImplementedError()  # pragma no cover

    def get_gateway_config_entities(
            self,
            version: str,
            namespace: Optional[str] = None,
            protection: Optional[RouteProtection] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[GatewayConfigEntity]:
        """
        Get the entities for the by-namespace templates.

        If namespace or purpose are None, then they act as wildcards.
        """
        raise NotImplementedError()  # pragma no cover

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
        raise NotImplementedError()  # pragma no cover

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
        raise NotImplementedError()  # pragma no cover
