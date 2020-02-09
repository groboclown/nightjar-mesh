from typing import Iterable, Tuple, Optional

from ..abc_collector import AbcCollectorDataStore


class S3Collector(AbcCollectorDataStore):
    def __init__(self):
        pass

    def get_service_color_templates(self) -> Iterable[Tuple[Optional[str], Optional[str], str, str]]:
        pass

    def get_namespace_templates(self) -> Iterable[Tuple[Optional[str], str, str]]:
        pass
