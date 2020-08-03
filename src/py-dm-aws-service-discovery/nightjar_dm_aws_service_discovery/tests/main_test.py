
"""
Test the main module
"""

import unittest
import os
import tempfile
import shutil
from .. import main


class MainTest(unittest.TestCase):
    """Test the main function."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.mkdtemp()
        self._out = os.path.join(self._temp_dir, 'x.txt')

    def tearDown(self) -> None:
        shutil.rmtree(self._temp_dir)

    def test_main_wrong_api_version(self) -> None:
        """Invoked main wrong."""
        ret = main.main([
            'main.py', '--action-file=' + self._out, '--api-version=abc',
        ])
        self.assertEqual(2, ret)

    def test_main_mesh(self) -> None:
        """Invoke main with mesh"""
        ret = main.main([
            'main.py', '--action-file=' + self._out, '--api-version=1',
        ])
        self.assertEqual(0, ret)
