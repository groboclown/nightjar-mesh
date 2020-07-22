
"""
Main program.
"""

from typing import List
import json
from . import get_gateway, get_service, get_mesh


ARG__OUTPUT_FILE = '--output-file='
ARG__MODE = '--mode='
ARG__API_VERSION = '--api-version='


def main(argv: List[str]) -> int:
    """Main program."""
    output_file = ''
    mode = ''

    for arg in argv[1:]:
        if arg.startswith(ARG__OUTPUT_FILE):
            output_file = arg[len(ARG__OUTPUT_FILE):].strip()
        elif arg.startswith(ARG__MODE):
            mode = arg[len(ARG__MODE):].strip()
        elif arg.startswith(ARG__API_VERSION):
            api_version = arg[len(ARG__API_VERSION):].strip()
            if api_version != '1':
                print('[dm-aws-ecs-tags] Unknown API version: ' + api_version)
                return 2

    if mode == 'gateway':
        data = get_gateway.get_gateway()
    elif mode == 'service':
        data = get_service.get_service()
    elif mode == 'mesh':
        data = get_mesh.get_mesh()
    else:
        print("[dm-aws-ecs-tags] Unknown operation mode: " + mode)
        return 2

    with open(output_file, 'w') as f:
        json.dump(data, f)

    return 0
