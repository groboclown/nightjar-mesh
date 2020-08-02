
"""Test for the main module."""

import unittest
import os
import tempfile
import shutil
import json
from .. import main


class MainTest(unittest.TestCase):
    """Test the main function."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self._temp_dir)

    def test_no_args(self) -> None:
        """Invoking the main function with no arguments."""
        ret = main.main(['main.py'])
        self.assertEqual(4, ret)

    def test_no_output_file(self) -> None:
        """Invoking the main function with no output-file argument."""
        ret = main.main(['main.py', '--api-version=1', '--mode=service'])
        self.assertEqual(2, ret)

    def test_wrong_version(self) -> None:
        """Invoking the main function with no output-file argument."""
        ret = main.main(['main.py', '--mode=service', '--output-file=x', '--api-version=abc'])
        self.assertEqual(4, ret)

    def test_mesh_mode(self) -> None:
        """Invoking the main function with mesh mode."""
        ret = main.main([
            'main.py', '--api-version=1', '--test=true',
            '--output-file=' + os.path.join(self._temp_dir, 'mesh.json'),
        ])
        self.assertEqual(0, ret)
        self.assertTrue(os.path.isfile(os.path.join(self._temp_dir, 'mesh.json')))
        with open(os.path.join(self._temp_dir, 'mesh.json'), 'r') as f:
            self.assertEqual({'mesh': True}, json.load(f))
