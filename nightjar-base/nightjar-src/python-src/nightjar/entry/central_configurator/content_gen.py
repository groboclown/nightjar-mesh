
from typing import Iterable, Dict, Tuple
import pystache  # type: ignore
from ...data_stores import (
    Entity,
    NamespaceEntity,
    ServiceColorEntity,
    CollectorDataStore,
    ConfigurationReaderDataStore,
    ConfigurationWriterDataStore,
)
from ...cloudmap_collector import EnvoyConfig
from ...msg import note


def generate_content(
        collector: CollectorDataStore,
        config_reader: ConfigurationReaderDataStore,
        config_writer: ConfigurationWriterDataStore,
        namespace_data: Iterable[Tuple[str, EnvoyConfig]],
        service_color_data: Iterable[Tuple[str, str, EnvoyConfig]],
) -> bool:
    diff = ContentDiff()
    diff.load_previous_entity_content(config_reader)
    generate_namespace_content(collector, diff, namespace_data)
    generate_service_color_content(collector, diff, service_color_data)
    return diff.write_if_different(config_writer)


class ContentDiff:
    """
    Stores content from previous and new versions of the configuration data.
    Storage is currently in memory, because we're estimating that the total size of the data is going to be
    small.  If this ends up being wrong, we can switch this over to temporary files.
    """
    previous_entity_content: Dict[Entity, str]
    current_entity_content: Dict[Entity, str]

    def __init__(self) -> None:
        self.previous_entity_content = {}
        self.current_entity_content = {}

    def load_previous_entity_content(self, reader: ConfigurationReaderDataStore) -> None:
        for n_entity in reader.list_namespace_entities():
            content = reader.download_entity_content(n_entity)
            if content:
                self.previous_entity_content[n_entity] = content
        for sc_entity in reader.list_service_color_entities():
            content = reader.download_entity_content(sc_entity)
            if content:
                self.previous_entity_content[sc_entity] = content

    def add_current_namespace_content(self, namespace: str, purpose: str, content: str) -> None:
        entity = NamespaceEntity(namespace, purpose, False)
        self.current_entity_content[entity] = content

    def add_current_service_color_content(self, service_color: Tuple[str, str], purpose: str, content: str) -> None:
        entity = ServiceColorEntity(service_color[0], service_color[1], purpose, False)
        self.current_entity_content[entity] = content

    def has_changed(self) -> bool:
        return self.previous_entity_content != self.current_entity_content

    def write_if_different(self, writer: ConfigurationWriterDataStore) -> bool:
        if not self.has_changed():
            note("No changes found between active version and current state")
            writer.no_change()
            return False
        note("Creating active version with new content.")
        for entity, content in self.current_entity_content.items():
            writer.set_entity_contents(entity, content)
        return True


def generate_namespace_content(
        collector: CollectorDataStore,
        diff: ContentDiff,
        namespace_data: Iterable[Tuple[str, EnvoyConfig]],
) -> None:
    namespace_configs = {}
    for namespace, config in namespace_data:
        namespace_configs[namespace] = config
    template_data = collector.get_namespace_templates(namespace_configs.keys())
    for namespace, purpose, template in template_data:
        content = pystache.render(template, namespace_configs[namespace].get_context())
        content_purpose = purpose
        if purpose.endswith('.mustache'):
            content_purpose = purpose[:-9]
        diff.add_current_namespace_content(namespace, content_purpose, content)


def generate_service_color_content(
        collector: CollectorDataStore,
        diff: ContentDiff,
        service_color_data: Iterable[Tuple[str, str, EnvoyConfig]],
) -> None:
    service_color_configs = {}
    for service, color, config in service_color_data:
        service_color_configs[(service, color)] = config
    template_data = collector.get_service_color_templates(service_color_configs.keys())
    for service_color, purpose, template in template_data:
        content = pystache.render(template, service_color_configs[service_color].get_context())
        content_purpose = purpose
        if purpose.endswith('.mustache'):
            content_purpose = purpose[:-9]
        diff.add_current_service_color_content(service_color, content_purpose, content)
