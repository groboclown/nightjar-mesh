
"""
Test the main module
"""

from typing import Any
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
        self._out = os.path.join(self._temp_dir, 'x.txt')
        self._orig_env = dict(os.environ)
        if 'NJ_DMLOCAL_BASE_DIR' in os.environ:
            del os.environ['NJ_DMLOCAL_BASE_DIR']  # pragma no cover
        if 'NJ_NAMESPACE' in os.environ:
            del os.environ['NJ_NAMESPACE']  # pragma no cover
        if 'NJ_SERVICE' in os.environ:
            del os.environ['NJ_SERVICE']  # pragma no cover
        if 'NJ_COLOR' in os.environ:
            del os.environ['NJ_COLOR']  # pragma no cover

    def tearDown(self) -> None:
        shutil.rmtree(self._temp_dir)
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_main_wrong_api_version(self) -> None:
        """Invoked main wrong."""
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--api-version=abc',
        ])
        self.assertEqual(4, ret)

    def test_main__no_file(self) -> None:
        """Invoke main with mesh"""
        os.environ['NJ_DMLOCAL_BASE_DIR'] = self._temp_dir
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--api-version=1',
        ])
        # No source file means it could, eventually, exist.
        self.assertEqual(31, ret)

    def test_main__valid(self) -> None:
        """Invoke main with mesh"""
        self._basic_file_setup()
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--api-version=1',
        ])
        self.assertEqual(0, ret)
        self.assertEqual({'mode': 'mesh'}, self._get_output())

    def test_main__no_files(self) -> None:
        """Invoke main with gateway"""
        os.environ['NJ_DMLOCAL_BASE_DIR'] = self._temp_dir
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--api-version=1',
        ])
        # No source file means it could, eventually, exist.
        self.assertEqual(31, ret)

    def _get_output(self) -> Any:
        self.assertTrue(os.path.isfile(self._out))
        with open(self._out, 'r') as f:
            return json.load(f)

    def _basic_file_setup(self) -> None:
        base_dir = os.path.join(self._temp_dir, 'files')
        os.makedirs(base_dir, exist_ok=True)
        out_file = os.path.join(base_dir, 'discovery-map.json')
        os.environ['NJ_DMLOCAL_DATA_FILE'] = out_file

        with open(out_file, 'w') as f:
            f.write('{"mode":"mesh"}')
