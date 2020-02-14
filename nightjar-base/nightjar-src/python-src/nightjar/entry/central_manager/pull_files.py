
from .file_mgr import (
    write_gateway_config_entity,
    write_service_id_config_entity,
    write_namespace_template_entity,
    write_service_color_template_entity,
)
from ...data_stores import (
    AbcDataStoreBackend,
    ManagerReadDataStore,
    as_gateway_config_entity,
    as_service_id_config_entity,
)


def pull_templates(backend: AbcDataStoreBackend, output_dir: str) -> None:
    with ManagerReadDataStore(backend) as reader:
        for entity_n in reader.get_namespace_templates():
            content = reader.get_template(entity_n)
            write_namespace_template_entity(output_dir, entity_n, content or '')
        for entity_s in reader.get_service_color_templates():
            content = reader.get_template(entity_s)
            write_service_color_template_entity(output_dir, entity_s, content or '')


def pull_generated_files(backend: AbcDataStoreBackend, output_dir: str) -> None:
    with ManagerReadDataStore(backend) as reader:
        for entity in reader.get_generated_files():
            content = reader.get_generated_file(entity)
            gc = as_gateway_config_entity(entity)
            if gc:
                write_gateway_config_entity(output_dir, gc, content or '')
                continue
            sc = as_service_id_config_entity(entity)
            assert sc
            write_service_id_config_entity(output_dir, sc, content or '')
