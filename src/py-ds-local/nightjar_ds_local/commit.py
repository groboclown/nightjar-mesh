
"""
Commit the data.
"""

import os
import json
import datetime
from .config import Config


def commit(config: Config, activity: str, source_file: str) -> int:
    """
    Commit the source file to the local store.
    """
    if not os.path.isfile(source_file):
        print(
            "[nightjar-ds-local] Requested commit for file {0} but it does not exist.".
            format(source_file)
        )
        return 1
    with open(source_file, 'r') as f:
        data = json.load(f)
    assert isinstance(data, dict)
    data['commit-version'] = datetime.datetime.utcnow().isoformat()

    if activity == 'configuration':
        dest_file = config.local_configuration_file
    elif activity == 'template':
        dest_file = config.local_template_file
    else:
        print("[nightjar-ds-local] Invalid activity: `{0}`".format(activity))
        return 5

    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    with open(dest_file, 'w') as f:
        json.dump(data, f)
    print("[nightjar-ds-local] Committed {0}".format(activity))
    return 0
