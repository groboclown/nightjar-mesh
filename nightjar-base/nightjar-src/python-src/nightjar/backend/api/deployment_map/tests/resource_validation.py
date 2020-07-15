
from typing import Dict, Any
import yaml
import jsonschema  # type: ignore
try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources  # type: ignore

from ... import deployment_map

SCHEMA_YAML = pkg_resources.read_text(deployment_map, 'service-data-schema.yaml')
SCHEMA = yaml.safe_load(SCHEMA_YAML)


def validate_envoy_config(config: Dict[str, Any]) -> None:
    jsonschema.validate(config, SCHEMA)
