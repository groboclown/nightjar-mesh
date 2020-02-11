
from typing import Iterable
import os
import time
import traceback
import sys
from .process import process_templates
from ...cloudmap_collector import DiscoveryServiceNamespace
from ...data_stores import AbcDataStoreBackend
from ...data_stores.s3 import create_s3_data_store


MAX_NAMESPACE_COUNT = 99


def main_loop(
        backend: AbcDataStoreBackend,
        namespace_names: Iterable[str],
        loop_sleep_time_seconds: int,
        exit_on_failure: bool,
) -> None:
    namespaces = DiscoveryServiceNamespace.load_namespaces(dict([
        (n, None) for n in namespace_names
    ]))

    while True:
        try:
            process_templates(backend, namespaces)
            time.sleep(loop_sleep_time_seconds)
        except BaseException as err:
            tb = traceback.format_exception(etype=type(err), value=err, tb=err.__traceback__)
            print('\n'.join(tb))
            if exit_on_failure:
                sys.exit(1)


def main() -> None:
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
    backend_name = os.environ['DATASTORE'].strip().lower()
    if backend_name == 's3':
        backend = create_s3_data_store()
    else:
        raise Exception('Unknown DATASTORE: "{0}"'.format(backend_name))

    main_loop(backend, namespace_names, loop_sleep_time, exit_on_failure)
