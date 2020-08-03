
"""
Fetch the data.
"""

import os
import json
from .config import Config


def fetch(config: Config, document: str, dst_file: str, previous_version: str) -> int:
    """Fetch the data from the store."""
    if document not in config.local_files:
        print("[nightjar-ds-local] Invalid activity `{0}`".format(document))
        return 5
    src_file = config.local_files[document]

    if not os.path.isfile(src_file):
        print("[nightjar-ds-local] No data for document {0}.".format(document))
        # It might appear later...
        return 31

    with open(src_file, 'r') as f:
        data = json.load(f)
    assert isinstance(data, dict)
    if previous_version and data['document-version'] == previous_version:
        return 30

    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    with open(dst_file, 'w') as f:
        json.dump(data, f)
    return 0
