
from typing import Iterable
from .input_data_gen import (
    load_namespace_data,
    load_service_color_data,
)
from .content_gen import (
    generate_content,
)

from ...cloudmap_collector import (
    DiscoveryServiceNamespace,
)
from ...data_stores import (
    AbcDataStoreBackend,
    CollectorDataStore,
    ConfigurationReaderDataStore,
    ConfigurationWriterDataStore,
)
from ...protect import RouteProtection, as_route_protection

# For now, we just have two hard-coded protections.
# This needs to be setup differently.
PUBLIC_PROTECTION = as_route_protection('public')
PRIVATE_PROTECTION = as_route_protection('private')
KNOWN_PROTECTIONS = (
    PUBLIC_PROTECTION,
    PRIVATE_PROTECTION,
)


def process_templates(
        backend: AbcDataStoreBackend,
        namespaces: Iterable[DiscoveryServiceNamespace],
        protections: Iterable[RouteProtection]
) -> None:
    """
    Process all the namespace and service/color templates into the envoy proxy content.

    This can potentially take up a lot of memory.  It's performing a trade-off of minimizing
    service calls for memory.
    """
    namespace_data = load_namespace_data(namespaces)
    service_color_data = load_service_color_data(namespaces)

    with CollectorDataStore(backend) as collector:
        with ConfigurationReaderDataStore(backend) as config_reader:
            with ConfigurationWriterDataStore(backend) as config_writer:
                generate_content(
                    collector, config_reader, config_writer,
                    namespace_data, service_color_data, protections,
                )
