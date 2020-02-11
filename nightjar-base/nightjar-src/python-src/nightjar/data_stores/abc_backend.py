

"""
Standard Prototype that the data stores must implement.
"""

from typing import Iterable, Optional, Union, Any
import abc

ACTIVITY_PROXY_CONFIGURATION = 'proxy-configuration'
ACTIVITY_TEMPLATE_DEFINITION = 'template-creation'

ENVOY_BOOTSTRAP_TEMPLATE_PURPOSE = 'envoy-bootstrap-template'


class NamespaceEntity:
    """
    Describes a namespace-based entity, which can optionally be the default namespace.

    Implementations can include information here about the generated lookup key, but
    care must be taken when using this for the "upload" functionality; any key
    in this object may not be trustworthy.
    """
    __slots__ = ('namespace', 'purpose', 'is_template',)

    def __init__(self, namespace: Optional[str], purpose: str, is_template: bool) -> None:
        self.namespace = namespace
        self.purpose = purpose
        self.is_template = is_template

    def is_default_namespace(self) -> bool:
        return self.namespace is None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NamespaceEntity):
            return False
        return (
            self.namespace == other.namespace
            and self.purpose == other.purpose
            and self.is_template == other.is_template
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.namespace) + hash(self.purpose) + hash(self.is_template)


class ServiceColorEntity:
    __slots__ = ('service', 'color', 'purpose', 'is_template',)

    def __init__(
            self, service: Optional[str], color: Optional[str], purpose: str, is_template: bool
    ) -> None:
        self.service = service
        self.color = color
        self.purpose = purpose
        self.is_template = is_template

    def is_default_service(self) -> bool:
        return self.service is None

    def is_default_color(self) -> bool:
        return self.color is None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ServiceColorEntity):
            return False
        return (
                self.service == other.service
                and self.color == other.color
                and self.purpose == other.purpose
                and self.is_template == other.is_template
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.service) + hash(self.color) + hash(self.purpose) + hash(self.is_template)


Entity = Union[ServiceColorEntity, NamespaceEntity]


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

    def download(self, version: str, entity: Entity) -> str:
        """Download the contents of the entry."""
        raise NotImplementedError()

    def upload(self, version: str, entity: Entity, contents: str) -> None:
        """Upload the given entry key with the given contents."""
        raise NotImplementedError()

    def get_namespace_entities(
            self,
            version: str,
            namespace: Optional[str] = None,
            purpose: Optional[str] = None,
            is_template: Optional[bool] = None,
    ) -> Iterable[NamespaceEntity]:
        """
        Get the entry key for the by-namespace store.

        "Purpose" is something like "envoy-template" or "cds".  If this is None, then the entry_name must be None,
        and the returned container key can only be used for `list_entries` call.

        If namespace is None, then the default value is used.

        If `entry_name` is not given, then this returns the container key for the namespace and purpose.
        Otherwise, it returns the entry key.
        """
        raise NotImplementedError()

    def get_service_color_entities(
            self,
            version: str,
            service: Optional[str] = None,
            color: Optional[str] = None,
            purpose: Optional[str] = None,
            is_template: Optional[bool] = None,
    ) -> Iterable[ServiceColorEntity]:
        """
        Get the entry keys for the by-service/color store.  Any option that is None means that the result
        should return all values that match everything else but this one.

        "Purpose" is something like "envoy-template" or "cds".
        """
        raise NotImplementedError()
