
"""
Find and load a JSON file.
"""

from typing import Dict, Sequence, Union
import os
import json
from .config import Config


def find_file(config: Config, request: str, paths: Sequence[str]) -> Union[int, Dict[str, str]]:
    """
    Use the config and request to populate the paths (using format), to
    find the first matching file.

    @param config:
    @param request:
    @param paths:
    @return:
    """
    for to_format in paths:
        filename = os.path.join(
            config.base_dir,
            to_format.format(
                request=request,
                namespace=config.namespace,
                service=config.service,
                color=config.color,
            )
        )
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                ret = json.load(f)
            assert isinstance(ret, dict)
            return ret

    print("[nightjar-dm-local] No such file for {0} / {1} / {2} / {3}".format(
        request, config.namespace, config.service, config.namespace,
    ))
    # It might appear later...
    return 31
