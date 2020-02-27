
import unittest
from .resource_validation import validate_envoy_config
from ..service_data import (
    EnvoyConfig,
    EnvoyCluster,
    EnvoyListener,
    EnvoyRoute,
    EnvoyClusterEndpoint,
)


class TestEnvoyConfig(unittest.TestCase):
    def test_schema_minimal(self) -> None:
        config = EnvoyConfig([
            EnvoyListener(None, [])
        ], [])
        validate_envoy_config(config.get_context('n', 's', None))
