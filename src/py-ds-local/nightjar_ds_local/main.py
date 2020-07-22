
"""
Single local file implementation of the data store extension point executable.
"""

from typing import List
import os
import json
import datetime


ENV_NAME__LOCAL_TEMPLATE_FILE = 'DM_LOCAL__TEMPLATE_FILE'
DEFAULT__LOCAL_TEMPLATE_FILE = '/etc/data-store/templates.json'
ENV_NAME__LOCAL_CONFIGURATION_FILE = 'DM_LOCAL__CONFIGURATION_FILE'
DEFAULT__LOCAL_CONFIGURATION_FILE = '/etc/data-store/configurations.json'

LOCAL_TEMPLATE_FILE = os.environ.get(
    ENV_NAME__LOCAL_TEMPLATE_FILE,
    DEFAULT__LOCAL_TEMPLATE_FILE,
)
LOCAL_CONFIGURATION_FILE = os.environ.get(
    ENV_NAME__LOCAL_CONFIGURATION_FILE,
    DEFAULT__LOCAL_CONFIGURATION_FILE,
)

ARG__ACTIVITY = '--activity='
ARG__PREVIOUS_VERSION = '--previous-document-version='
ARG__ACTION = '--action='
ARG__FILE = '--action-file='
ARG__API_VERSION = '--api-version='


def main(argv: List[str]) -> int:
    """Main execution."""
    activity = ''
    previous_version = ''
    action = ''
    action_file = ''

    for arg in argv[1:]:
        if arg.startswith(ARG__ACTIVITY):
            activity = arg[len(ARG__ACTIVITY):].strip()
        elif arg.startswith(ARG__PREVIOUS_VERSION):
            previous_version = arg[len(ARG__PREVIOUS_VERSION):].strip()
        elif arg.startswith(ARG__ACTION):
            action = arg[len(ARG__ACTION):].strip()
        elif arg.startswith(ARG__FILE):
            action = arg[len(ARG__FILE):].strip()
        elif arg.startswith(ARG__API_VERSION):
            api_version = arg[len(ARG__API_VERSION):].strip()
            if api_version != '1':
                raise Exception('Unknown API version: ' + api_version)

    if action == 'commit':
        if not os.path.isfile(action_file):
            print("[nightjar-ds-local] Requested commit for file {0} but it does not exist.".format(action_file))
            return 2
        with open(action_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        data['commit-version'] = datetime.datetime.utcnow().isoformat()

        if activity == 'configuration':
            dest_file = LOCAL_CONFIGURATION_FILE
        elif activity == 'template':
            dest_file = LOCAL_TEMPLATE_FILE
        else:
            print("[nightjar-ds-local] Invalid activity: `{0}`".format(activity))
            return 2

        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        with open(dest_file, 'w') as f:
            json.dump(data, f)
        print("[nightjar-ds-local] Committed {0}".format(activity))
        return 0

    elif action == 'fetch':
        if activity == 'configuration':
            src_file = LOCAL_CONFIGURATION_FILE
        elif activity == 'template':
            src_file = LOCAL_TEMPLATE_FILE
        else:
            print("[nightjar-ds-local] Invalid activity `{0}`".format(activity))
            return 2

        if not os.path.isfile(src_file):
            print("[nightjar-ds-local] No data for activity {0}.".format(activity))
            return 2

        with open(src_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        if previous_version and data['commit-version'] == previous_version:
            # print("[nightjar-ds-local] No data updates for activity {0}.".format(activity))
            return 3

        os.makedirs(os.path.dirname(action_file), exist_ok=True)
        with open(action_file, 'w') as f:
            json.dump(data, f)
        return 0

    else:
        print("[nightjar-ds-local] Invalid action `{0}`.".format(action))
        return 2
