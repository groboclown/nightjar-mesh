
"""
Single local file implementation of the data store extension point executable.
"""

from typing import List
from .config import create_configuration
from .commit import commit
from .fetch import fetch


ARG__ACTIVITY = '--activity='
ARG__PREVIOUS_VERSION = '--previous-document-version='
ARG__ACTION = '--action='
ARG__FILE = '--action-file='
ARG__API_VERSION = '--api-version='


def main(argv: List[str]) -> int:
    """Main execution."""
    config = create_configuration()
    activity = ''
    previous_version = ''
    action = ''
    action_file = ''
    api_version = ''

    for arg in argv[1:]:
        if arg.startswith(ARG__ACTIVITY):
            activity = arg[len(ARG__ACTIVITY):].strip()
        elif arg.startswith(ARG__PREVIOUS_VERSION):
            previous_version = arg[len(ARG__PREVIOUS_VERSION):].strip()
        elif arg.startswith(ARG__ACTION):
            action = arg[len(ARG__ACTION):].strip()
        elif arg.startswith(ARG__FILE):
            action_file = arg[len(ARG__FILE):].strip()
        elif arg.startswith(ARG__API_VERSION):
            api_version = arg[len(ARG__API_VERSION):].strip()

    if api_version != '1':
        print('[dm-aws-service-discovery] Unknown API version: ' + api_version)
        return 4

    if action == 'commit':
        return commit(config, activity, action_file)

    if action == 'fetch':
        return fetch(config, activity, action_file, previous_version)

    print("[nightjar-ds-local] Invalid action `{0}`.".format(action))
    return 6
