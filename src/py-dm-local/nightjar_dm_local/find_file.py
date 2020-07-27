
"""
Find and load a JSON file.
"""

from typing import Dict, Union
import os
import json
from .config import Config


def find_file(config: Config) -> Union[int, Dict[str, str]]:
    """
    Use the config to find the matching file.

    @param config:
    @return:
    """
    if not os.path.isfile(config.data_file):
        print("[nightjar-dm-local] No such file: {0}".format(config.data_file))
        # It might appear later...
        return 31
    with open(config.data_file, 'r') as f:
        ret = json.load(f)
    assert isinstance(ret, dict)
    return ret
