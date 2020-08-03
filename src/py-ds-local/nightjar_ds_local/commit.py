
"""
Commit the data.
"""

import os
import json
import datetime
from .config import Config


def commit(config: Config, document: str, source_file: str) -> int:
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
    version = datetime.datetime.utcnow().isoformat()
    data['commit-version'] = version

    dst_file = config.get_file(document)
    if not dst_file:
        print("[nightjar-ds-local] Invalid document: `{0}`".format(document))
        return 5

    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    with open(dst_file, 'w') as f:
        json.dump(data, f)
    print("[nightjar-ds-local] Committed {0}".format(document))
    return 0
