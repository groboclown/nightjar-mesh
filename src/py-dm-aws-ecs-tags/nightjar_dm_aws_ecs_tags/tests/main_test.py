
"""Test for the main module."""

import unittest
from .. import main


class MainTest(unittest.TestCase):
    """Test the main function."""

    def test_no_args(self) -> None:
        """Invoking the main function with no arguments."""
        ret = main.main([])
        self.assertEqual(2, ret)
