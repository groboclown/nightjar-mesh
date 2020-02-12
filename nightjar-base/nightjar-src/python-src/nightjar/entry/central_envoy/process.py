
from typing import Iterable, Tuple, Callable, Optional
import os
from ...data_stores import AbcDataStoreBackend, EnvoyProxyDataStore
from ...msg import debug


def process_contents(
        get_envoy_files: Callable[[EnvoyProxyDataStore], Iterable[Tuple[str, Optional[str]]]],
        get_envoy_bootstrap_template: Callable[[EnvoyProxyDataStore], Optional[str]],
        backend: AbcDataStoreBackend, admin_port: str, listener_port: str,
        envoy_bootstrap_file: str, output_dir: str,
) -> None:
    with EnvoyProxyDataStore(backend) as envoy_proxy:
        purpose_files = {}

        # TODO unify these groups together.  It makes nightjar more flexible.

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

        template_contents = get_envoy_bootstrap_template(envoy_proxy)
        if template_contents:
            contents = (
                template_contents
                # TODO should this hard-coded path replacement be more flexible?
                .replace('%admin_port%', admin_port)
                .replace('%listener_port%', listener_port)
            )
            output_file = os.path.join(output_dir, envoy_bootstrap_file)
            debug("Generating file {p}", p=output_file)
            with open(output_file, 'w') as f:
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
