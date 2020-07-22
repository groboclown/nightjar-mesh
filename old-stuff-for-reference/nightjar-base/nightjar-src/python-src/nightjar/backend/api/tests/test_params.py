
"""Tests for the params module"""

import unittest
from ..params import ParamDef


class ParamDefTest(unittest.TestCase):
    """ParamDef tests"""
    def test_required_not_given(self) -> None:
        """Should fail if required parameters are not given."""
        p_d = ParamDef('n1', 'N1', ['n1'], '', None, str, True)
        try:
            p_d.get_value({})
            self.fail('Did not raise ValueError.')
        except ValueError:
            pass

    def test_required_not_given_with_default(self) -> None:
        """Parameters with defaults is okay, and the defaults are used."""
        p_d = ParamDef('n1', 'N1', ['n1'], '', 'xyz', str, True)
        self.assertEqual(p_d.get_value({}), 'xyz')

    def test_not_required_not_given(self) -> None:
        """Parameters without defaults but not required are okay."""
        p_d = ParamDef('n1', 'N1', ['n1'], '', None, str, False)
        self.assertIsNone(p_d.get_value({}))
