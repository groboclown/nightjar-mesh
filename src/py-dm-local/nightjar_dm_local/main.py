
"""
Main program.
"""

from typing import List
import json
from .config import create_configuration
from .find_file import find_file


ARG__OUTPUT_FILE = '--output-file='
ARG__MODE = '--mode='
ARG__API_VERSION = '--api-version='


REQUEST_PATHS = {
    'mesh': (
        'mesh.json',
    ),
    'gateway': (
        'gateway/{namespace}.json',
        'gateway/default.json',
    ),
    'service': (
        'service/{namespace}-{service}-{color}.json',
        'service/{namespace}-{service}-default.json',
        'service/{namespace}-default-{color}.json',
        'service/{namespace}-default-default.json',
        'service/default-{service}-{color}.json',
        'service/default-{service}-default.json',
        'service/default-default-{color}.json',
        'service/default-default-default.json',
    ),
}


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

    if api_version != '1':
        print('[dm-aws-service-discovery] Unknown API version: ' + api_version)
        return 4

    if mode not in REQUEST_PATHS:
        print("[dm-aws-service-discovery] Unknown operation mode: " + mode)
        return 1

    data = find_file(config, mode, REQUEST_PATHS[mode])

    if isinstance(data, int):
        return data

    with open(output_file, 'w') as f:
        json.dump(data, f)

    return 0
