
"""
Main program.
"""

from typing import List
import json
from . import get_mesh


ARG__OUTPUT_FILE = '--action-file='
ARG__API_VERSION = '--api-version='
# This version ignores the --previous-document-version= argument.


def main(argv: List[str]) -> int:
    """Main program."""
    output_file = ''
    api_version = ''

    for arg in argv[1:]:
        if arg.startswith(ARG__OUTPUT_FILE):
            output_file = arg[len(ARG__OUTPUT_FILE):].strip()
        elif arg.startswith(ARG__API_VERSION):
            api_version = arg[len(ARG__API_VERSION):].strip()
    if api_version != '1':
        print('[dm-aws-service-discovery] Unknown API version: ' + api_version)
        return 2

    data = get_mesh.get_mesh()

    with open(output_file, 'w') as f:
        json.dump(data, f)

    return 0
