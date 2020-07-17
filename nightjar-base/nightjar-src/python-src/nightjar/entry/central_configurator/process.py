
"""
Process templates.
"""

from typing import Iterable
from ...backend.api.deployment_map import AbcDeploymentMap
from .content_gen import (
    generate_content,
)
from .input_data_gen import load_service_color_data, load_namespace_data

from ...backend.api.data_store import (
    AbcDataStoreBackend,
    CollectorDataStore,
    ConfigurationReaderDataStore,
    ConfigurationWriterDataStore,
)
from ...protect import RouteProtection


def process_templates(
        backend: AbcDataStoreBackend,
        deployment_map: AbcDeploymentMap,
        namespaces: Iterable[str],
        namespace_protections: Iterable[RouteProtection],
        service_protection: RouteProtection,
) -> None:
    """
    Process all the namespace and service/color templates into the envoy proxy content.

    This can potentially take up a lot of memory.  It's performing a trade-off of minimizing
    service calls for memory.
    """
    namespace_data = load_namespace_data(deployment_map, namespaces, namespace_protections)
    service_color_data = load_service_color_data(deployment_map, namespaces, service_protection)

    with CollectorDataStore(backend) as collector:
        with ConfigurationReaderDataStore(backend) as config_reader:
            with ConfigurationWriterDataStore(backend) as config_writer:
                generate_content(
                    collector, config_reader, config_writer,
                    namespace_data, service_color_data,
                    namespace_protections,
                )
