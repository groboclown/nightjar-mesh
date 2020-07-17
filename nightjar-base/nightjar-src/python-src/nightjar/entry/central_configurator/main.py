
"""
Main program for the central configurator.
"""

from typing import Iterable
import os
import time
import traceback
import sys
import gc
from .process import process_templates
from ...backend.api.data_store import AbcDataStoreBackend
from ...backend.impl.data_store import get_data_store_impl, get_data_store_params
from ...backend.api.deployment_map import AbcDeploymentMap
from ...backend.impl.deployment_map import get_deployment_map_impl, get_deployment_map_params
from ...protect import RouteProtection, PROTECTION_PRIVATE, PROTECTION_PUBLIC
from ...msg import debug
from ...mem import report_current_memory_usage


KNOWN_PROTECTIONS = (PROTECTION_PUBLIC, PROTECTION_PRIVATE)

MAX_NAMESPACE_COUNT = 99


def main_loop(
        backend: AbcDataStoreBackend,
        deployment_map: AbcDeploymentMap,
        namespace_names: Iterable[str],
        namespace_protections: Iterable[RouteProtection],
        loop_sleep_time_seconds: int,
        exit_on_failure: bool,
        one_pass: bool
) -> None:
    """Infinite loop for the central configurator."""
    while True:
        try:
            debug("Starting template processing.")
            process_templates(backend, deployment_map, namespace_names, namespace_protections, PROTECTION_PRIVATE)
            gc.collect()
            report_current_memory_usage()
            if one_pass:
                return
            time.sleep(loop_sleep_time_seconds)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as err:
            tb = traceback.format_exception(etype=type(err), value=err, tb=err.__traceback__)
            print('\n'.join(tb))
            if one_pass or exit_on_failure:
                sys.exit(1)
            time.sleep(loop_sleep_time_seconds)


def get_data_store() -> AbcDataStoreBackend:
    """Gets the configured data store implementation."""
    data_store_params = get_data_store_params()
    data_store_name = os.environ['DATASTORE'].strip().lower()
    for param in data_store_params:
        if data_store_name in param.aliases:
            return get_data_store_impl(param.name, param.parse_env_values())
    raise Exception('Unknown DATASTORE: "{0}"'.format(data_store_name))


def get_deployment_map(namespace_names: Iterable[str]) -> AbcDeploymentMap:
    """Gets the deployment map implementation."""
    deployment_map_params = get_deployment_map_params()
    deployment_map_name = os.environ['DEPLOYMENTMAP'].strip().lower()
    for param in deployment_map_params:
        if deployment_map_name in param.aliases:
            return get_deployment_map_impl(param.name, param.parse_env_values(), namespace_names)
    raise Exception('Unknown DEPLOYMENTMAP: "{0}"'.format(deployment_map_name))


def main() -> None:
    """Program entry point."""
    loop_sleep_time = int(os.environ.get('REFRESH_TIME', '30'))
    exit_on_failure = os.environ.get('EXIT_ON_FAILURE', 'false').strip().lower() in (
        'true', 'yes', 'on', 'enabled', 'active', '1',
    )

    namespace_names = []
    for i in range(0, MAX_NAMESPACE_COUNT + 1):
        namespace = os.environ.get('NAMESPACE_{0}'.format(i), None)
        if namespace:
            namespace = namespace.strip()
            if namespace:
                namespace_names.append(namespace)

    data_store = get_data_store()
    deployment_map = get_deployment_map(namespace_names)

    one_pass = len(sys.argv) > 1 and sys.argv[1] == 'one-pass'
    # TODO make KNOWN_PROTECTIONS configurable.
    main_loop(
        data_store, deployment_map,
        namespace_names, KNOWN_PROTECTIONS,
        loop_sleep_time, exit_on_failure, one_pass
    )
