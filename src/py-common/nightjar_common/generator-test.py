#!/usr/bin/python3

"""
Simple CLI Tool for transforming the discovery-map into the proxy input format.
Used for testing.
"""

import os
import sys
import json
from nightjar_common.envoy_transform import gateway, service

ARG__NAMESPACE = '--namespace='
ARG__SERVICE = '--service='
ARG__COLOR = '--color='
ARG__FILE = '--file='


def main() -> None:
    """The Main method"""
    output_format = 'none'
    namespace = 'default'
    service_name = 'default'
    color_name = 'default'
    file_name = 'none'

    for arg in sys.argv[1:]:
        if arg in ('gateway', 'service',):
            output_format = arg
        elif arg.startswith(ARG__NAMESPACE):
            namespace = arg[len(ARG__NAMESPACE):]
        elif arg.startswith(ARG__SERVICE):
            service_name = arg[len(ARG__SERVICE):]
        elif arg.startswith(ARG__COLOR):
            color_name = arg[len(ARG__COLOR):]
        elif arg.startswith(ARG__FILE):
            file_name = arg[len(ARG__FILE):]

    if not os.path.isfile(file_name):
        print("Could not find discovery-map file: " + repr(file_name))
        sys.exit(1)

    with open(file_name, 'r') as f:
        data = json.load(f)

    if output_format == 'gateway':
        print(json.dumps(gateway.create_gateway_proxy_input(data, namespace, 9900, 9901)))
        sys.exit(0)

    if output_format == 'service':
        print(json.dumps(service.create_service_color_proxy_input(
            data, namespace, service_name, color_name, 9900, 9901,
        )))
        sys.exit(0)

    print(
        (
            "Usage: {name} (gateway|service) {f}(discovery-map file) "
            "{n}(namespace) [{s}service] [{c}color]"
        ).format(name=sys.argv[0], f=ARG__FILE, n=ARG__NAMESPACE, s=ARG__SERVICE, c=ARG__COLOR)
    )


if __name__ == '__main__':
    main()
