
from typing import Iterable, Tuple, Optional
from .abc_backend import (
    AbcDataStoreBackend,
    ACTIVITY_PROXY_CONFIGURATION,
    ENVOY_BOOTSTRAP_TEMPLATE_PURPOSE,
)


class EnvoyProxyDataStore:
    """
    API used by the envoy proxy servers for updating the configuration.  These have
    limit read-only usage.
    """
    def __init__(self, backend: AbcDataStoreBackend) -> None:
        self.backend = backend
        self.__version = backend.get_active_version(ACTIVITY_PROXY_CONFIGURATION)

    def get_namespace_envoy_bootstrap_template(self, namespace: str) -> str:
        """
        Returns the envoy bootstrap file for the namespace.

        The returned template will have `{{key}}` in the text, where key is a key from the returned
        envoy files.  The caller must replace that text with the corresponding key's file path.

        Because if the well-known and simple values in this template, regular expressions, simple find-replace,
        or mustache can be used to update the template.

        If the bootstrap file changes while Envoy is running, then the envoy proxy itself will
        need to be restarted.
        """
        # Content files MUST be stored exactly, no default is allowed.
        entities = self.backend.get_namespace_entities(
            self.__version,
            namespace=namespace,
            purpose=ENVOY_BOOTSTRAP_TEMPLATE_PURPOSE,
            # This is classified as content, not a template, because it has already been
            # transformed by the configuration phase.
            is_template=False
        )

        # Use the first entity found.
        for entity in entities:
            return self.backend.download(self.__version, entity)
        # If there were no entities found, then this is an error.
        raise ValueError('No envoy bootstrap found for namespace {0}'.format(namespace))

    def get_service_color_envoy_bootstrap_template(self, service: str, color: str) -> str:
        """
        Returns the envoy bootstrap file for the service/color.

        The returned template will have `{{key}}` in the text, where key is a key from the returned
        envoy files.  The caller must replace that text with the corresponding key's file path.

        Because if the well-known and simple values in this template, regular expressions, simple find-replace,
        or mustache can be used to update the template.

        If the bootstrap file changes while Envoy is running, then the envoy proxy itself will
        need to be restarted.
        """
        # Content files MUST be stored exactly, no default is allowed.
        entities = self.backend.get_service_color_entities(
            self.__version,
            service=service,
            color=color,
            purpose=ENVOY_BOOTSTRAP_TEMPLATE_PURPOSE,
            is_template=False
        )
        for entity in entities:
            return self.backend.download(self.__version, entity)
        raise ValueError('No envoy bootstrap found for service {0}, color {1}'.format(service, color))

    def get_namespace_envoy_files(self, namespace: str) -> Iterable[Tuple[str, Optional[str]]]:
        """
        Returns the list of (key, contents) for the dynamic envoy files of the namespace.
        If the bootstrap template requires a key and there is no
        content, then it must be returned with None data.
        """
        for entity in self.backend.get_namespace_entities(self.__version, namespace=namespace, is_template=False):
            if entity.purpose == ENVOY_BOOTSTRAP_TEMPLATE_PURPOSE:
                continue
            yield entity.purpose, self.backend.download(self.__version, entity)

    def get_service_color_envoy_files(self, service: str, color: str) -> Iterable[Tuple[str, Optional[str]]]:
        """
        Returns the list of (key, contents) for the dynamic envoy files of the service/color.
        If the bootstrap template requires a key and there is no
        content, then it must be returned with None data.
        """
        for entity in self.backend.get_service_color_entities(
                self.__version, service=service, color=color, is_template=False
        ):
            if entity.purpose == ENVOY_BOOTSTRAP_TEMPLATE_PURPOSE:
                continue
            yield entity.purpose, self.backend.download(self.__version, entity)
