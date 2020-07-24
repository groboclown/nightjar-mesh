
"""
Test the main module.
"""

import unittest
from .. import main


class MainTest(unittest.TestCase):
    """Test the main function."""

    def test_main__no_arguments(self) -> None:
        """Stupid simple invocation."""
        self.assertEqual(0, main.main(['main.py']))
