
"""
Test the generate module.
"""

from typing import List, Dict, Optional, Any
import unittest
import os
import platform
import shutil
import json
from .. import generate
from ..config import (
    Config,
    ENV__DATA_STORE_EXEC, ENV__DISCOVERY_MAP_EXEC,
)


class GenerateDataImplTest(unittest.TestCase):
    """Test the generator functions and classes."""
    # These are all smashed together, because they share the same setup and teardown logic.
    # Yeah, it's a lousy reason to jam them together, but it makes less duplication.

    def setUp(self) -> None:
        noop_cmd = 'where' if platform.system() == 'Windows' else 'echo'
        python_cmd = 'python' if platform.system() == 'Windows' else 'python3'
        self._runnable = [
            python_cmd,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runnable.py'),
        ]
        self._config = Config({
            ENV__DISCOVERY_MAP_EXEC: noop_cmd,
            ENV__DATA_STORE_EXEC: noop_cmd,
        })
        self._gen_file = os.path.join(self._config.temp_dir, 'generated-discovery-map.json')
        self._old_file = os.path.join(self._config.temp_dir, 'last-discovery-map.json')
        self._file_index = 0

    def tearDown(self) -> None:
        shutil.rmtree(self._config.temp_dir)

    def test_create_generator(self) -> None:
        """Test the create generator with a gateway request."""
        res = generate.create_generator(self._config)
        self.assertIsInstance(res, generate.GenerateDataImpl)

    def test_is_generated_map_different__no_files(self) -> None:
        """Test is_generated_map_different with no files"""
        self.assertFalse(os.path.isfile(self._gen_file))
        self.assertFalse(os.path.isfile(self._old_file))
        gen = generate.GenerateDataImpl(self._config)
        res = gen.is_generated_map_different()
        self.assertFalse(res)

    def test_is_generated_map_different__just_new(self) -> None:
        """Test is_generated_map_different with no files"""
        with open(self._gen_file, 'w') as f:
            json.dump({}, f)
        self.assertFalse(os.path.isfile(self._old_file))
        gen = generate.GenerateDataImpl(self._config)
        res = gen.is_generated_map_different()
        self.assertTrue(res)

    def test_is_generated_map_different__just_old(self) -> None:
        """Test is_generated_map_different with no files"""
        with open(self._old_file, 'w') as f:
            json.dump({}, f)
        self.assertFalse(os.path.isfile(self._gen_file))
        gen = generate.GenerateDataImpl(self._config)
        res = gen.is_generated_map_different()
        self.assertFalse(res)

    def test_is_generated_map_different__same(self) -> None:
        """Test is_generated_map_different with no files"""
        with open(self._gen_file, 'w') as f:
            json.dump({'x': True}, f)
        with open(self._old_file, 'w') as f:
            json.dump({'x': True}, f)
        gen = generate.GenerateDataImpl(self._config)
        res = gen.is_generated_map_different()
        self.assertFalse(res)

    def test_is_generated_map_different__different(self) -> None:
        """Test is_generated_map_different with no files"""
        with open(self._gen_file, 'w') as f:
            json.dump({'x': True}, f)
        with open(self._old_file, 'w') as f:
            json.dump({'y': True}, f)
        gen = generate.GenerateDataImpl(self._config)
        res = gen.is_generated_map_different()
        self.assertTrue(res)

    def test_commit_discovery_map__with_error(self) -> None:
        """Test commit_discovery_map with an error"""
        self._config.data_store_exec = self._get_runnable_cmd(1, self._gen_file, {
            'schema-version': 'v1',
            'document-version': 'x',
            'namespaces': [],
        })
        gen = generate.GenerateDataImpl(self._config)
        res = gen.commit_discovery_map()
        self.assertEqual(1, res)
        self.assertFalse(os.path.isfile(self._old_file))

    def test_commit_discovery_map__no_gen_file(self) -> None:
        """Test commit_discovery_map with no gen file"""
        self.assertFalse(os.path.isfile(self._gen_file))
        gen = generate.GenerateDataImpl(self._config)
        res = gen.commit_discovery_map()
        self.assertEqual(0, res)
        self.assertFalse(os.path.isfile(self._old_file))

    def test_commit_discovery_map__success(self) -> None:
        """Test commit_discovery_map successful run."""
        self.assertFalse(os.path.isfile(self._old_file))
        expected = {
            'schema-version': 'v1',
            'document-version': 'a',
            'namespaces': [],
        }
        self._config.data_store_exec = self._get_runnable_cmd(0, self._gen_file, expected)
        gen = generate.GenerateDataImpl(self._config)
        res = gen.commit_discovery_map()
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(self._old_file))
        with open(self._old_file, 'r') as f:
            self.assertEqual(expected, json.load(f))

    def test_generate_discovery_map__failure(self) -> None:
        """Test generate_discovery_map which fails to execute."""
        self._config.discovery_map_exec = self._get_runnable_cmd(6, None, {})
        gen = generate.GenerateDataImpl(self._config)
        res = gen.generate_discovery_map()
        self.assertEqual(1, res)
        self.assertFalse(os.path.isfile(self._gen_file))

    def test_update_discovery_map__failure_gen(self) -> None:
        """Test update_discovery_map with failure form discovery map."""
        self._config.discovery_map_exec = self._get_runnable_cmd(6, None, {})
        self._config.data_store_exec = self._get_runnable_cmd(12, None, {})
        gen = generate.GenerateDataImpl(self._config)
        res = gen.update_discovery_map()
        self.assertEqual(1, res)

    def test_update_discovery_map__failure_commit(self) -> None:
        """Test update_discovery_map with failure form discovery map."""
        self._config.discovery_map_exec = self._get_runnable_cmd(0, None, {})
        self._config.data_store_exec = self._get_runnable_cmd(6, None, {})
        gen = generate.GenerateDataImpl(self._config)
        res = gen.update_discovery_map()
        self.assertEqual(1, res)

    def test_update_discovery_map__no_change(self) -> None:
        """Test update_discovery_map with no changed contents."""
        expected = {
            'schema-version': 'v1',
            'document-version': 'z',
            'namespaces': [],
        }
        with open(self._old_file, 'w') as f:
            json.dump(expected, f)
        self._config.discovery_map_exec = self._get_runnable_cmd(0, None, expected)
        # data-store should not run, so have it generate an error if it does.
        self._config.data_store_exec = self._get_runnable_cmd(1, None, {})
        gen = generate.GenerateDataImpl(self._config)
        res = gen.update_discovery_map()
        self.assertEqual(0, res)

    def test_update_discovery_map__changed(self) -> None:
        """Test update_discovery_map with changed contents."""
        with open(self._old_file, 'w') as f:
            json.dump({
                'schema-version': 'v1',
                'document-version': 'old',
                'namespaces': [],
            }, f)
        expected = {
            'schema-version': 'v1',
            'document-version': 'new',
            'namespaces': [],
        }
        self._config.discovery_map_exec = self._get_runnable_cmd(0, None, expected)
        self._config.data_store_exec = self._get_runnable_cmd(0, None, {})
        gen = generate.GenerateDataImpl(self._config)
        res = gen.update_discovery_map()
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(self._old_file))
        with open(self._old_file, 'r') as f:
            self.assertEqual(expected, json.load(f))

    def _get_runnable_cmd(
            self, exit_code: int, filename: Optional[str], src_contents: Dict[str, Any],
    ) -> List[str]:
        ret = list(self._runnable)
        ret.append(str(exit_code))
        self._file_index += 1
        if filename:
            out = filename
        else:
            out = os.path.join(self._config.temp_dir, '{0}-src.json'.format(self._file_index))
        with open(out, 'w') as f:
            json.dump(src_contents, f)
        ret.append(out)
        return ret
