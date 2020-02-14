
import os
from .process import process_namespace, process_service_color
from ...data_stores.s3 import create_s3_data_store


def main() -> None:
    out_dir = os.environ['OUTPUT_DIR'].strip()
    os.makedirs(out_dir, exist_ok=True)
    envoy_bootstrap_file = os.environ['ENVOY_BOOTSTRAP_FILE'].strip()
    admin_port = os.environ['ADMIN_PORT'].strip()
    listener_port = os.environ['LISTENER_PORT'].strip()
    namespace = os.environ.get('GATEWAY_NAMESPACE')
    service_id = os.environ.get('SERVICE_ID')
    protection = os.environ.get('PUBLIC', 'NO')
    if protection.strip().lower() in ('yes', 'active', 'public', 'on', 'enable', 'enabled', '1'):
        is_public = True
    else:
        is_public = False

    backend_name = os.environ['DATASTORE'].strip().lower()
    if backend_name == 's3':
        backend = create_s3_data_store()
    else:
        raise Exception('Unknown DATASTORE: "{0}"'.format(backend_name))

    if namespace:
        if service_id:
            raise ValueError('Must specify GATEWAY_NAMESPACE or (SERVICE and COLOR), not both.')
        process_namespace(
            namespace.strip(),is_public,
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
