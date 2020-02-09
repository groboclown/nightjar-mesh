

"""
Standard Prototype that the data stores must implement.
The API is broken up by use case, so there may be duplication between the classes.
"""

from typing import Iterable, Tuple, Optional
import abc


class AbcCollectorDataStore(abc.ABC):
    """
    API used by the collectors, which read the AWS service information and transform that with the
    configuration to create files used by the envoy proxy.
    """

    def get_service_color_templates(self) -> Iterable[Tuple[Optional[str], Optional[str], str, str]]:
        """
        Returns (service name, service color, key, contents).  See above for interpretation of None
        service names and colors.
        """
        raise NotImplementedError()

    def get_namespace_templates(self) -> Iterable[Tuple[Optional[str], str, str]]:
        """
        Returns (namespace, key, contents), where "namespace" is either the name, ID (prefixed with 'id:'), ARN,
        or None (indicating that it's the default namespace).
        """
        raise NotImplementedError()
