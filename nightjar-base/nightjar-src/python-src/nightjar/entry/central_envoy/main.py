
import os
from .process import process_namespace, process_service_color
from ...backend.api.data_store import AbcDataStoreBackend
from ...backend.impl.data_store import get_data_store_params, get_data_store_impl
from ...protect import as_route_protection


def get_data_store() -> AbcDataStoreBackend:
    data_store_params = get_data_store_params()
    data_store_name = os.environ['DATASTORE'].strip().lower()
    for param in data_store_params:
        if data_store_name in param.aliases:
            return get_data_store_impl(param.name, param.parse_env_values())
    raise Exception('Unknown DATASTORE: "{0}"'.format(data_store_name))


def main() -> None:
    out_dir = os.environ['OUTPUT_DIR'].strip()
    os.makedirs(out_dir, exist_ok=True)
    admin_port = os.environ['ADMIN_PORT'].strip()
    listener_port = os.environ['LISTENER_PORT'].strip()
    namespace = os.environ.get('GATEWAY_NAMESPACE')
    service_id = os.environ.get('SERVICE_ID')
    protection = as_route_protection(os.environ.get('PROTECTION', 'public'))

    backend = get_data_store()

    if namespace:
        if service_id:
            raise ValueError('Must specify GATEWAY_NAMESPACE or (SERVICE and COLOR), not both.')
        process_namespace(
            namespace.strip(), protection,
            backend, admin_port, listener_port, out_dir,
        )
    elif service_id:
        # above if shows that namespace not given, so don't need to check.
        process_service_color(
            service_id.strip(),
            backend, admin_port, listener_port, out_dir
        )
    else:
        raise ValueError('Must specify one of GATEWAY_NAMESPACE or (SERVICE and COLOR).')
