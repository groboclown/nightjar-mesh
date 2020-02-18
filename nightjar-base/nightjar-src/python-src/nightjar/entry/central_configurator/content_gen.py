
from typing import Iterable, Dict, Tuple, Union, Any
import pystache  # type: ignore
from ...backend.api.data_store import (
    ConfigEntity,
    CollectorDataStore,
    ConfigurationReaderDataStore,
    ConfigurationWriterDataStore,
    GatewayConfigEntity,
    ServiceIdConfigEntity,
    MatchedServiceColorTemplate,
    MatchedNamespaceTemplate,
)
from ...backend.api.deployment_map import EnvoyConfig
from ...protect import RouteProtection
from ...msg import note


def generate_content(
        collector: CollectorDataStore,
        config_reader: ConfigurationReaderDataStore,
        config_writer: ConfigurationWriterDataStore,
        namespace_data: Iterable[Tuple[str, EnvoyConfig]],
        service_color_data: Iterable[Tuple[str, str, str, str, EnvoyConfig]],
        protections: Iterable[RouteProtection],
) -> bool:
    """
    service_color_data items are:
        namespace_id, service_id, service, color, config
    """
    diff = ContentDiff()
    diff.load_previous_entity_content(config_reader)
    generate_namespace_content(collector, diff, namespace_data, protections)
    generate_service_color_content(collector, diff, service_color_data)
    return diff.write_if_different(config_writer)


class ContentDiff:
    """
    Stores content from previous and new versions of the configuration data.
    Storage is currently in memory, because we're estimating that the total size of the data is going to be
    small.  If this ends up being wrong, we can switch this over to temporary files.
    """
    previous_entity_content: Dict[ConfigEntity, str]
    current_entity_content: Dict[ConfigEntity, str]

    def __init__(self) -> None:
        self.previous_entity_content = {}
        self.current_entity_content = {}

    def load_previous_entity_content(self, reader: ConfigurationReaderDataStore) -> None:
        for n_entity in reader.list_config_entities():
            content = reader.download_entity_content(n_entity)
            if content:
                self.previous_entity_content[n_entity] = content

    def add_current_namespace_content(
            self, namespace: str, protection: RouteProtection, purpose: str, content: str
    ) -> None:
        entity = GatewayConfigEntity(namespace, protection, purpose)
        self.current_entity_content[entity] = content

    def add_current_service_id_content(
            self, namespace_id: str, service_id: str, service_color: Tuple[str, str], purpose: str, content: str
    ) -> None:
        entity = ServiceIdConfigEntity(namespace_id, service_id, service_color[0], service_color[1], purpose)
        self.current_entity_content[entity] = content

    def has_changed(self) -> bool:
        return self.previous_entity_content != self.current_entity_content

    def write_if_different(self, writer: ConfigurationWriterDataStore) -> bool:
        if not self.has_changed():
            note("No changes found between active version and current state")
            writer.no_change()
            return False
        note("Creating active version with new content.")

        # DEBUG CODE --------------------------------------------------------
        # remaining_old = set(self.previous_entity_content.keys())
        # for newv, newc in self.current_entity_content.items():
        #     if newv in remaining_old:
        #         remaining_old.remove(newv)
        #         if newc != self.previous_entity_content[newv]:
        #             debug("Content differs for {c}:\n{v}", c=newv, v=newc)
        #     else:
        #         debug("New content not in old: {c}", c=newv)
        # for old in remaining_old:
        #     debug("Old content not in new: {c}", c=old)
        # -------------------------------------------------------------------

        for entity, content in self.current_entity_content.items():
            writer.set_entity_contents(entity, content)
        return True


def generate_namespace_content(
        collector: CollectorDataStore,
        diff: ContentDiff,
        namespace_data: Iterable[Tuple[str, EnvoyConfig]],
        protections: Iterable[RouteProtection]
) -> None:
    namespace_configs = {}
    for namespace, config in namespace_data:
        for protection in protections:
            namespace_configs[(namespace, protection)] = config
    template_data = collector.get_namespace_templates(namespace_configs.keys())
    for match, template in template_data:
        config = namespace_configs[(match.namespace_id, match.protection)]
        content, content_purpose = render_content(
            match, template, config.get_context('gateway', 'gateway', None)
        )
        diff.add_current_namespace_content(match.namespace_id, match.protection, content_purpose, content)


def generate_service_color_content(
        collector: CollectorDataStore,
        diff: ContentDiff,
        service_color_data: Iterable[Tuple[str, str, str, str, EnvoyConfig]],
) -> None:
    """
    service_color_data items are:
        namespace_id, service_id, service, color, config
    """

    service_color_configs = {}
    for namespace_id, service_id, service, color, config in service_color_data:
        service_color_configs[(namespace_id, service_id, service, color)] = config
    template_data = collector.get_service_color_templates(service_color_configs.keys())
    for match, template in template_data:
        config = service_color_configs[(match.namespace_id, match.service_id, match.service, match.color)]
        content, content_purpose = render_content(
            match, template, config.get_context(
                match.namespace_id,
                '{0}-{1}'.format(match.service, match.color),
                None
            )
        )
        diff.add_current_service_id_content(
            match.namespace_id, match.service_id,
            (match.service, match.color), content_purpose, content
        )


def render_content(
        match: Union[MatchedServiceColorTemplate, MatchedNamespaceTemplate],
        template: str, config: Dict[str, Any]
) -> Tuple[str, str]:
    # TODO should the transformation happen for ALL content, or just
    #   .mustache template purposes?
    content = pystache.render(template, config)
    content_purpose = match.purpose
    if match.purpose.endswith('.mustache'):
        content_purpose = match.purpose[:-9]
    return content, content_purpose
