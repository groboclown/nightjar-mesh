
from typing import Iterable, Tuple, Callable, Optional
import os
from ...backend.api.data_store import AbcDataStoreBackend, EnvoyProxyDataStore
from ...protect import RouteProtection
from ...msg import debug


def process_contents(
        get_envoy_files: Callable[[EnvoyProxyDataStore], Iterable[Tuple[str, Optional[str]]]],
        backend: AbcDataStoreBackend, admin_port: str, listener_port: str,
        output_dir: str,
) -> None:
    with EnvoyProxyDataStore(backend) as envoy_proxy:
        purpose_files = {}

        for purpose, template_contents in get_envoy_files(envoy_proxy):
            if template_contents:
                contents = (
                    template_contents
                    # TODO should this hard-coded path replacement be more flexible?
                    .replace('%admin_port%', admin_port)
                    .replace('%listener_port%', listener_port)
                )
                output_file = os.path.join(output_dir, purpose)
                debug("Writing file {p}", p=output_file)
                purpose_files[purpose] = output_file
                with open(output_file, 'w') as f:
                    f.write(contents)


def process_namespace(
        namespace_id: str, protection: RouteProtection,
        backend: AbcDataStoreBackend, admin_port: str, listener_port: str,
        output_dir: str,
) -> None:
    process_contents(
        lambda envoy_proxy: envoy_proxy.get_gateway_envoy_files(namespace_id, protection),
        backend, admin_port, listener_port, output_dir,
    )


def process_service_color(
        service_id: str,
        backend: AbcDataStoreBackend, admin_port: str, listener_port: str,
        output_dir: str,
) -> None:
    process_contents(
        lambda envoy_proxy: envoy_proxy.get_service_envoy_files(service_id),
        backend, admin_port, listener_port, output_dir,
    )
