
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

    def test_main_wrong_operation(self) -> None:
        """Invoked main wrong."""
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=y', '--api-version=1',
        ])
        self.assertEqual(1, ret)

    def test_main_wrong_api_version(self) -> None:
        """Invoked main wrong."""
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=gateway', '--api-version=abc',
        ])
        self.assertEqual(4, ret)

    def test_main_mesh__no_file(self) -> None:
        """Invoke main with mesh"""
        os.environ['NJ_DMLOCAL_BASE_DIR'] = self._temp_dir
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=mesh', '--api-version=1',
        ])
        # No source file means it could, eventually, exist.
        self.assertEqual(31, ret)

    def test_main_mesh__valid(self) -> None:
        """Invoke main with mesh"""
        self._basic_file_setup()
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=mesh', '--api-version=1',
        ])
        self.assertEqual(0, ret)
        self.assertEqual({'mode': 'mesh'}, self._get_output())

    def test_main_gateway__no_files(self) -> None:
        """Invoke main with gateway"""
        os.environ['NJ_DMLOCAL_BASE_DIR'] = self._temp_dir
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=gateway', '--api-version=1',
        ])
        # No source file means it could, eventually, exist.
        self.assertEqual(31, ret)

    def test_main_gateway__has_namespace(self) -> None:
        """Invoke main with gateway"""
        self._basic_file_setup()
        os.environ['NJ_NAMESPACE'] = 'n1'
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=gateway', '--api-version=1',
        ])
        self.assertEqual(0, ret)
        self.assertEqual(
            {'mode': 'gateway', 'namespace': 'n1'},
            self._get_output(),
        )

    def test_main_gateway__namespace_not_exist(self) -> None:
        """Invoke main with gateway"""
        self._basic_file_setup()
        os.environ['NJ_NAMESPACE'] = 'n2'
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=gateway', '--api-version=1',
        ])
        self.assertEqual(0, ret)
        self.assertEqual(
            {'mode': 'gateway', 'namespace': 'default'},
            self._get_output(),
        )

    def test_main_gateway__has_default(self) -> None:
        """Invoke main with gateway"""
        self._basic_file_setup()
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=gateway', '--api-version=1',
        ])
        self.assertEqual(0, ret)
        self.assertEqual(
            {'mode': 'gateway', 'namespace': 'default'},
            self._get_output(),
        )

    def test_main_service__no_files(self) -> None:
        """Invoke main with service"""
        os.environ['NJ_DMLOCAL_BASE_DIR'] = self._temp_dir
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=service', '--api-version=1',
        ])
        # No source file means it could, eventually, exist.
        self.assertEqual(31, ret)

    def test_main_service__all_defaults(self) -> None:
        """Invoke main with service"""
        self._basic_file_setup()
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=service', '--api-version=1',
        ])
        self.assertEqual(0, ret)
        self.assertEqual(
            {'color': 'default', 'mode': 'service', 'namespace': 'default', 'service': 'default'},
            self._get_output(),
        )

    def test_main_service__all_not_found(self) -> None:
        """Invoke main with service"""
        os.environ['NJ_NAMESPACE'] = 'n2'
        os.environ['NJ_SERVICE'] = 's2'
        os.environ['NJ_COLOR'] = 'c2'
        self._basic_file_setup()
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=service', '--api-version=1',
        ])
        self.assertEqual(0, ret)
        self.assertEqual(
            {'color': 'default', 'mode': 'service', 'namespace': 'default', 'service': 'default'},
            self._get_output(),
        )

    def test_main_service__all_found(self) -> None:
        """Invoke main with service"""
        os.environ['NJ_NAMESPACE'] = 'n1'
        os.environ['NJ_SERVICE'] = 's1'
        os.environ['NJ_COLOR'] = 'blue'
        self._basic_file_setup()
        ret = main.main([
            'main.py', '--output-file=' + self._out, '--mode=service', '--api-version=1',
        ])
        self.assertEqual(0, ret)
        self.assertEqual(
            {'color': 'blue', 'mode': 'service', 'namespace': 'n1', 'service': 's1'},
            self._get_output(),
        )

    def _get_output(self) -> Any:
        self.assertTrue(os.path.isfile(self._out))
        with open(self._out, 'r') as f:
            return json.load(f)

    def _basic_file_setup(self) -> None:
        base_dir = os.path.join(self._temp_dir, 'files')
        gateway_dir = os.path.join(base_dir, 'gateway')
        service_dir = os.path.join(base_dir, 'service')
        os.environ['NJ_DMLOCAL_BASE_DIR'] = base_dir
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(gateway_dir, exist_ok=True)
        os.makedirs(service_dir, exist_ok=True)

        with open(os.path.join(base_dir, 'mesh.json'), 'w') as f:
            f.write('{"mode":"mesh"}')
        with open(os.path.join(base_dir, 'gateway', 'default.json'), 'w') as f:
            f.write('{"mode":"gateway", "namespace":"default"}')
        with open(os.path.join(base_dir, 'gateway', 'n1.json'), 'w') as f:
            f.write('{"mode":"gateway", "namespace":"n1"}')
        with open(os.path.join(base_dir, 'service', 'default-default-default.json'), 'w') as f:
            f.write(
                '{"mode":"service", "namespace":"default", "service":"default", "color":"default"}'
            )
        with open(os.path.join(base_dir, 'service', 'default-default-blue.json'), 'w') as f:
            f.write(
                '{"mode":"service", "namespace":"default", "service":"default", "color":"blue"}'
            )
        with open(os.path.join(base_dir, 'service', 'default-s1-default.json'), 'w') as f:
            f.write('{"mode":"service", "namespace":"default", "service":"s1", "color":"default"}')
        with open(os.path.join(base_dir, 'service', 'default-s1-blue.json'), 'w') as f:
            f.write('{"mode":"service", "namespace":"default", "service":"s1", "color":"blue"}')
        with open(os.path.join(base_dir, 'service', 'n1-default-blue.json'), 'w') as f:
            f.write('{"mode":"service", "namespace":"n1", "service":"default", "color":"blue"}')
        with open(os.path.join(base_dir, 'service', 'n1-s1-default.json'), 'w') as f:
            f.write('{"mode":"service", "namespace":"n1", "service":"s1", "color":"default"}')
        with open(os.path.join(base_dir, 'service', 'n1-s1-blue.json'), 'w') as f:
            f.write('{"mode":"service", "namespace":"n1", "service":"s1", "color":"blue"}')
