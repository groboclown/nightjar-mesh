
"""
Main program.
"""

from typing import List
import json
from .config import create_configuration
from .find_file import find_file


ARG__OUTPUT_FILE = '--output-file='
ARG__API_VERSION = '--api-version='


def main(argv: List[str]) -> int:
    """Main program."""
    output_file = ''
    api_version = ''

    config = create_configuration()

    for arg in argv[1:]:
        if arg.startswith(ARG__OUTPUT_FILE):
            output_file = arg[len(ARG__OUTPUT_FILE):].strip()
        elif arg.startswith(ARG__API_VERSION):
            api_version = arg[len(ARG__API_VERSION):].strip()

    if api_version != '1':
        print('[dm-aws-service-discovery] Unknown API version: ' + api_version)
        return 4

    data = find_file(config)

    if isinstance(data, int):
        return data

    with open(output_file, 'w') as f:
        json.dump(data, f)

    return 0
