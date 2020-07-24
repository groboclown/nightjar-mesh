
"""
Fetch the data.
"""

import os
import json
from .config import Config


def fetch(config: Config, activity: str, dest_file: str, previous_version: str) -> int:
    """Fetch the data from the store."""
    if activity == 'configuration':
        src_file = config.local_configuration_file
    elif activity == 'template':
        src_file = config.local_template_file
    else:
        print("[nightjar-ds-local] Invalid activity `{0}`".format(activity))
        return 5

    if not os.path.isfile(src_file):
        print("[nightjar-ds-local] No data for activity {0}.".format(activity))
        # It might appear later...
        return 31

    with open(src_file, 'r') as f:
        data = json.load(f)
    assert isinstance(data, dict)
    if previous_version and data['commit-version'] == previous_version:
        # print("[nightjar-ds-local] No data updates for activity {0}.".format(activity))
        return 3

    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    with open(dest_file, 'w') as f:
        json.dump(data, f)
    return 0
