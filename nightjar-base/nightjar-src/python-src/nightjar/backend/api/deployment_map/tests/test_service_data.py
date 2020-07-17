
"""
Test the service_data module.
"""

import unittest
from .resource_validation import validate_envoy_config
from ..service_data import (
    EnvoyConfig,
    EnvoyListener,
)


class TestEnvoyConfig(unittest.TestCase):
    """Tests for EnvoyConfig."""

    def test_schema_minimal(self) -> None:  # pylint: disable=R0201
        """Minimal schema."""
        config = EnvoyConfig([EnvoyListener(None, [])], [])
        validate_envoy_config(config.get_context('n', 's', None))
