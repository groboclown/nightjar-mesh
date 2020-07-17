
"""Standalone program entry point."""

import json
from .input_data_gen import get_envoy_config

if __name__ == '__main__':
    print(json.dumps(get_envoy_config()))
