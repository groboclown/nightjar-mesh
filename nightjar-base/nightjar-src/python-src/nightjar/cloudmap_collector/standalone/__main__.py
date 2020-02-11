import json
from .input_data_gen import create_envoy_config

if __name__ == '__main__':
    print(json.dumps(create_envoy_config().get_context()))
