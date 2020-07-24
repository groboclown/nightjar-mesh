
"""
Test the main module.
"""

import unittest
from .. import main


class MainTest(unittest.TestCase):
    """Test the main function."""

    def test_main_no_args(self) -> None:
        """Run main with no arguments."""
        self.assertEqual(0, main.main(['main.py']))
