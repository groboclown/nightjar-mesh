
"""
Test the parse_env module.
"""

import unittest
from .. import parse_env


class ParseEnvTest(unittest.TestCase):
    """Test the parse_env functions."""

    def test_env_as_int__not_set(self) -> None:
        """env value not set"""
        self.assertEqual(
            -10,
            parse_env.env_as_int({}, 'tuna', -10),
        )

    def test_env_as_int__not_int(self) -> None:
        """env value not an int"""
        self.assertEqual(
            100,
            parse_env.env_as_int({'tuna': 'fish'}, 'tuna', 100),
        )

    def test_env_as_int__int(self) -> None:
        """env value is an int"""
        self.assertEqual(
            123,
            parse_env.env_as_int({'koi': '123'}, 'koi', 5),
        )

    def test_env_as_float__not_set(self) -> None:
        """env value not set"""
        self.assertEqual(
            -10.5,
            parse_env.env_as_float({}, 'tuna', -10.5),
        )

    def test_env_as_float__not_float(self) -> None:
        """env value not a float"""
        self.assertEqual(
            100.9,
            parse_env.env_as_float({'tuna': 'fish'}, 'tuna', 100.9),
        )

    def test_env_as_float__float(self) -> None:
        """env value is a float"""
        self.assertEqual(
            123.4,
            parse_env.env_as_float({'koi': '123.4'}, 'koi', 5),
        )

    def test_env_as_bool__not_set(self) -> None:
        """env value is not set"""
        self.assertTrue(
            parse_env.env_as_bool({}, 'bat', True),
        )

    def test_env_as_bool__not_true_or_false(self) -> None:
        """env value is set to non-boolean value"""
        self.assertTrue(
            parse_env.env_as_bool({'bat': 'wing'}, 'bat', True),
        )

    def test_env_as_bool__true(self) -> None:
        """env value is set to a true value."""
        self.assertTrue(
            parse_env.env_as_bool({'bat': 'TRUE'}, 'bat', False),
        )

    def test_env_as_bool__false(self) -> None:
        """env value is set to a false value"""
        self.assertFalse(
            parse_env.env_as_bool({'bat': 'off'}, 'bat', True),
        )
