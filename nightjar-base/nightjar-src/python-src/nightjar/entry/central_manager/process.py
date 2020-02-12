
from typing import Iterable, Tuple, Optional
import os
from ...data_stores import (
    AbcDataStoreBackend,
    ManagerDataStore,
)

DEFAULT_NAME = '__default__'


def get_namespace_templates(base_dir: str) -> Iterable[Tuple[Optional[str], str, str]]:
    template_dir = os.path.join(base_dir, 'namespace')
    if os.path.isdir(template_dir):
        for namespace_name in os.listdir(template_dir):
            if namespace_name.startswith('.'):
                continue
            namespace_dir = os.path.join(template_dir, namespace_name)
            if not os.path.isdir(namespace_dir):
                continue
            upload_name: Optional[str] = namespace_name
            if namespace_name == DEFAULT_NAME:
                upload_name = None
            for purpose_name in os.listdir(namespace_dir):
                purpose_filename = os.path.join(namespace_dir, purpose_name)
                if not os.path.isfile(purpose_filename):
                    continue
                with open(purpose_filename, 'r') as f:
                    yield upload_name, purpose_name, f.read()


def get_service_color_templates(base_dir: str) -> Iterable[Tuple[Optional[str], Optional[str], str, str]]:
    template_dir = os.path.join(base_dir, 'service')
    if os.path.isdir(template_dir):
        for service_name in os.listdir(template_dir):
            if service_name.startswith('.'):
                continue
            service_dir = os.path.join(template_dir, service_name)
            if not os.path.isdir(service_dir):
                continue
            upload_service_name: Optional[str] = service_name
            if service_name == DEFAULT_NAME:
                upload_service_name = None
            for color_name in os.listdir(service_dir):
                if color_name.startswith('.'):
                    continue
                color_dir = os.path.join(service_dir, color_name)
                if not os.path.isdir(color_dir):
                    continue
                upload_color_name: Optional[str] = color_name
                if color_name == DEFAULT_NAME:
                    upload_color_name = None
                for purpose_name in os.listdir(color_dir):
                    purpose_filename = os.path.join(color_dir, purpose_name)
                    if not os.path.isfile(purpose_filename):
                        continue
                    with open(purpose_filename, 'r') as f:
                        yield upload_service_name, upload_color_name, purpose_name, f.read()


def process(backend: AbcDataStoreBackend, base_dir: str) -> None:
    with ManagerDataStore(backend) as manager:
        for namespace, purpose, contents in get_namespace_templates(base_dir):
            manager.set_namespace_template(namespace, purpose, contents)
        for service, color, purpose, contents in get_service_color_templates(base_dir):
            manager.set_service_color_template(service, color, purpose, contents)
