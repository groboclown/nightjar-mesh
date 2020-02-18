
from .file_mgr import find_templates
from ...backend.api.data_store import (
    AbcDataStoreBackend,
    ManagerWriteDataStore,
)


def push_templates(backend: AbcDataStoreBackend, base_dir: str) -> None:
    with ManagerWriteDataStore(backend) as manager:
        for entity, contents in find_templates(base_dir):
            manager.set_template(entity, contents)
