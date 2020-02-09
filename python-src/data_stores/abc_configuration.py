

"""
Standard Prototype that the data stores must implement. The API is broken up by
use case, so there may be duplication between the classes.
"""

from typing import Iterable, Tuple, Optional


class AbcConfigurationDataStore:
    """
    API used by tools that need to read and write the envoy templates used to construct the envoy files.
    """
    def set_service_color_template(
            self,
            template_key: str, template_contents: str,
            service: Optional[str], color: Optional[str]
    ) -> None:
        """
        Writes the template for the given key associated with the service/color.  The translation logic
        should interpret the optional service and key as:
            Request for service+color must have a template.  If the data store contains an exact match for
            service+color, use that.  Then if the data store contains an exact match for service but None color,
            use that.  Otherwise, use the None service/None color.
        If service is None, then color must be None.  This does not support a generic per-color template.
        """
        raise NotImplementedError()

    def get_service_color_template(
            self,
            template_key: str,
            service: Optional[str], color: Optional[str]
    ) -> Optional[str]:
        raise NotImplementedError()

    def remove_service_color_template(
            self,
            template_key: str,
            service: Optional[str], color: Optional[str]
    ) -> bool:
        raise NotImplementedError()

    def set_namespace_template(
            self,
            template_key: str, template_contents: str,
            namespace: Optional[str]
    ) -> None:
        raise NotImplementedError()

    def get_namespace_template(
            self,
            template_key: str,
            namespace: Optional[str]
    ) -> Optional[str]:
        raise NotImplementedError()

    def remove_namespace_template(
            self,
            template_key: str,
            namespace: Optional[str]
    ) -> bool:
        raise NotImplementedError()

    def set_service_color_envoy_bootstrap(
            self,
            contents: str,
            service: Optional[str], color: Optional[str]
    ) -> None:
        raise NotImplementedError()

    def get_service_color_envoy_bootstrap(
            self,
            service: Optional[str], color: Optional[str]
    ) -> Optional[str]:
        raise NotImplementedError()

    def remove_service_color_envoy_bootstrap(
            self,
            service: Optional[str], color: Optional[str]
    ) -> bool:
        raise NotImplementedError()

    def set_namespace_envoy_bootstrap(self, contents: str, namespace: Optional[str]) -> None:
        raise NotImplementedError()

    def get_namespace_envoy_bootstrap(self, namespace: Optional[str]) -> Optional[str]:
        raise NotImplementedError()

    def remove_namespace_envoy_bootstrap(self, namespace: Optional[str]) -> bool:
        raise NotImplementedError()
