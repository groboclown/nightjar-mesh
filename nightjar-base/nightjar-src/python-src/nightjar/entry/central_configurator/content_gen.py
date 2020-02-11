
from typing import Iterable, Tuple
import pystache
from ...data_stores import (
    CollectorDataStore,
    ConfigurationDataStore,
)
from ...cloudmap_collector import EnvoyConfig


def generate_namespace_content(
        collector: CollectorDataStore,
        configuration: ConfigurationDataStore,
        namespace_data: Iterable[Tuple[str, EnvoyConfig]],
) -> None:
    namespace_configs = {}
    for namespace, config in namespace_data:
        namespace_configs[namespace] = config
    template_data = collector.get_namespace_templates(namespace_configs.keys())
    for namespace, purpose, template in template_data:
        content = pystache.render(template, namespace_configs[namespace].get_context())
        configuration.set_namespace_purpose_contents(namespace, purpose, content)


def generate_service_color_content(
        collector: CollectorDataStore,
        configuration: ConfigurationDataStore,
        service_color_data: Iterable[Tuple[str, str, EnvoyConfig]],
) -> None:
    service_color_configs = {}
    for service, color, config in service_color_data:
        service_color_configs[(service, color)] = config
    template_data = collector.get_service_color_templates(service_color_configs.keys())
    for service_color, purpose, template in template_data:
        content = pystache.render(template, service_color_configs[service_color].get_context())
        configuration.set_service_color_purpose_contents(service_color[0], service_color[1], purpose, content)
