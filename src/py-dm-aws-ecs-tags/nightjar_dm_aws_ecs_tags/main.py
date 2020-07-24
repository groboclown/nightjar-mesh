
"""
Main program.
"""

from typing import List
import json
from . import get_gateway, get_service, get_mesh
from .config import create_configuration


ARG__OUTPUT_FILE = '--output-file='
ARG__MODE = '--mode='
ARG__API_VERSION = '--api-version='

# Internal usage only
ARG__TEST = '--test=true'


def main(argv: List[str]) -> int:
    """Main program."""
    output_file = ''
    mode = ''
    api_version = ''
    config = create_configuration()

    for arg in argv[1:]:
        if arg.startswith(ARG__OUTPUT_FILE):
            output_file = arg[len(ARG__OUTPUT_FILE):].strip()
        elif arg.startswith(ARG__MODE):
            mode = arg[len(ARG__MODE):].strip()
        elif arg.startswith(ARG__API_VERSION):
            api_version = arg[len(ARG__API_VERSION):].strip()
        elif arg == ARG__TEST:
            config.test_mode = True

    if api_version != '1':
        print('[dm-aws-ecs-tags] Unknown API version: ' + api_version)
        return 4

    if not output_file:
        print('[dm-aws-ecs-tags] No --output-file given')
        return 2

    if mode == 'gateway':
        data = get_gateway.get_gateway(config)
    elif mode == 'service':
        data = get_service.get_service(config)
    elif mode == 'mesh':
        data = get_mesh.get_mesh(config)
    else:
        print("[dm-aws-ecs-tags] Unknown operation mode: " + mode)
        return 3

    if isinstance(data, int):
        return data

    with open(output_file, 'w') as f:
        json.dump(data, f)

    return 0
