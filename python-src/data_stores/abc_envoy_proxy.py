

"""
Standard Prototype that the data stores must implement.  The API is broken up by
use case, so there may be duplication between the classes.
"""

from typing import Iterable, Tuple, Optional


class AbcEnvoyProxyDataStore:
    """
    API used by the envoy proxy servers for updating the configuration.  These have
    limit read-only usage.
    """

    def get_envoy_bootstrap_template(
            self, namespace: Optional[str] = None, service_color: Optional[Tuple[str, str]] = None
    ) -> str:
        """
        Returns the envoy bootstrap file for the namespace or service-color (exactly one must be given).
        The returned template will have `{{key}}` in the text, where key is a key from the returned
        envoy files.  The caller must replace that text with the corresponding key's file path.

        Because if the well-known and simple values in this template, regular expressions, simple find-replace,
        or mustache can be used to update the template.
        """
        raise NotImplementedError()

    def get_envoy_keys(
            self, namespace: Optional[str] = None, service_color: Optional[Tuple[str, str]] = None
    ) -> Iterable[str]:
        """
        Returns just the keys for the bootstrap template.  This is useful if the file needs to have some
        idea about what the initial setup.
        """
        raise NotImplementedError()

    def get_envoy_files(
            self, namespace: Optional[str] = None, service_color: Optional[Tuple[str, str]] = None
    ) -> Iterable[Tuple[str, Optional[str]]]:
        """
        Returns the list of (key, contents) for the dynamic envoy files of the namespace or service-color
        (exactly one must be given).  If the bootstrap template requires a key and there is no
        content, then it must be returned with None data.
        """
        raise NotImplementedError()
