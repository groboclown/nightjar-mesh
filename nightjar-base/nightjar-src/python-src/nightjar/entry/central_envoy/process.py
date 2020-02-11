
from typing import Iterable, Tuple, Callable
import os
from ...data_stores import AbcDataStoreBackend, EnvoyProxyDataStore


def process_contents(
        get_envoy_files: Callable[[EnvoyProxyDataStore], Iterable[Tuple[str, str]]],
        get_envoy_bootstrap_template: Callable[[EnvoyProxyDataStore], str],
        backend: AbcDataStoreBackend, admin_port: str, listener_port: str,
        envoy_bootstrap_file: str, output_dir: str,
) -> None:
    envoy_proxy = EnvoyProxyDataStore(backend)

    purpose_files = {}
    for purpose, contents in get_envoy_files(envoy_proxy):
        output_file = os.path.join(output_dir, purpose)
        purpose_files[purpose] = output_file
        with open(output_file, 'w') as f:
            f.write(contents)

    with open(envoy_bootstrap_file, 'w') as f:
        template_contents = get_envoy_bootstrap_template(envoy_proxy)
        contents = (
            template_contents
            .replace('%admin_port%', admin_port)
            .replace('%listener_port%', listener_port)
        )
        f.write(contents)


def process_namespace(
        namespace: str,
        backend: AbcDataStoreBackend, admin_port: str, listener_port: str,
        envoy_bootstrap_file: str, output_dir: str,
) -> None:
    process_contents(
        lambda envoy_proxy: envoy_proxy.get_namespace_envoy_files(namespace),
        lambda envoy_proxy: envoy_proxy.get_namespace_envoy_bootstrap_template(namespace),
        backend, admin_port, listener_port, envoy_bootstrap_file, output_dir,
    )


def process_service_color(
        service: str, color: str,
        backend: AbcDataStoreBackend, admin_port: str, listener_port: str,
        envoy_bootstrap_file: str, output_dir: str,
) -> None:
    process_contents(
        lambda envoy_proxy: envoy_proxy.get_service_color_envoy_files(service, color),
        lambda envoy_proxy: envoy_proxy.get_service_color_envoy_bootstrap_template(service, color),
        backend, admin_port, listener_port, envoy_bootstrap_file, output_dir,
    )
