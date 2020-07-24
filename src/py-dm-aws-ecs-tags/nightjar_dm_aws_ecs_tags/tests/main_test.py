
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

    def test_no_mode(self) -> None:
        """Invoking the main function with no mode argument."""
        ret = main.main(['main.py', '--api-version=1', '--output-file=x'])
        self.assertEqual(3, ret)

    def test_wrong_version(self) -> None:
        """Invoking the main function with no output-file argument."""
        ret = main.main(['main.py', '--mode=service', '--output-file=x', '--api-version=abc'])
        self.assertEqual(4, ret)

    def test_bad_mode(self) -> None:
        """Invoking the main function with unknown mode."""
        ret = main.main(['main.py', '--api-version=1', '--output-file=x', '--mode=xyz'])
        self.assertEqual(3, ret)

    def test_service_mode(self) -> None:
        """Invoking the main function with service mode."""
        ret = main.main([
            'main.py', '--api-version=1', '--test=true',
            '--output-file=' + os.path.join(self._temp_dir, 'service.json'),
            '--mode=service',
        ])
        self.assertEqual(23, ret)
        self.assertFalse(os.path.isfile(os.path.join(self._temp_dir, 'service.json')))

    def test_gateway_mode(self) -> None:
        """Invoking the main function with gateway mode."""
        ret = main.main([
            'main.py', '--api-version=1', '--test=true',
            '--output-file=' + os.path.join(self._temp_dir, 'gateway.json'),
            '--mode=gateway',
        ])
        self.assertEqual(0, ret)
        self.assertTrue(os.path.isfile(os.path.join(self._temp_dir, 'gateway.json')))
        with open(os.path.join(self._temp_dir, 'gateway.json'), 'r') as f:
            self.assertEqual({'gateway': True}, json.load(f))

    def test_mesh_mode(self) -> None:
        """Invoking the main function with mesh mode."""
        ret = main.main([
            'main.py', '--api-version=1', '--test=true',
            '--output-file=' + os.path.join(self._temp_dir, 'mesh.json'),
            '--mode=mesh',
        ])
        self.assertEqual(0, ret)
        self.assertTrue(os.path.isfile(os.path.join(self._temp_dir, 'mesh.json')))
        with open(os.path.join(self._temp_dir, 'mesh.json'), 'r') as f:
            self.assertEqual({'mesh': True}, json.load(f))
