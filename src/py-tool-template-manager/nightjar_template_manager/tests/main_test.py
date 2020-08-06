
"""Test the main module."""

from typing import Dict, List, Any
import unittest
import os
import re
import tempfile
import shutil
import json
import platform
from nightjar_common.extension_point.errors import ExtensionPointRuntimeError
from .. import main


class MainTest(unittest.TestCase):
    """Test the main function.  It ends up testing a lot more than just main..."""

    def setUp(self) -> None:
        noop_cmd = 'where' if platform.system() == 'Windows' else 'which'
        self._runnable = [noop_cmd]
        self._temp_dir = tempfile.mkdtemp()
        self._file_index = 1

    def tearDown(self) -> None:
        shutil.rmtree(self._temp_dir)

    def test_main__no_action(self) -> None:
        """Test the main program with no action.  This is just ensuring that ConfigParser
        is setup to do what it does."""
        config_file = self._setup_config({})
        try:
            main.main(['main.py', '-C', config_file])
            self.fail('ConfigParser should have raised an error')  # pragma no cover
        except SystemExit as err:
            self.assertEqual(2, err.code)

    def test_main__document_list_action(self) -> None:
        """Test the main program with no action.  This is just ensuring that ConfigParser
        is setup to do what it does."""
        config_file = self._setup_config({})
        res = main.main(['main.py', '-C', config_file, '--document-type', 'other', 'list'])
        self.assertEqual(1, res)

    def test_main__push_template_no_purpose(self) -> None:
        """Test the main program with push, but no purpose.  We're not testing the
        actual details of the invocation, just that it's invoked."""
        config_file = self._setup_config(_mk_templates([], []))
        res = main.main(['main.py', '-C', config_file, 'push'])
        self.assertEqual(3, res)

    def test_main__pull_template_no_purpose(self) -> None:
        """Test the main program with pull, but no purpose.  We're not testing the
        actual details of the invocation, just that it's invoked."""
        config_file = self._setup_config(_mk_templates([], []))
        res = main.main(['main.py', '-C', config_file, 'pull'])
        self.assertEqual(6, res)

    def test_main__push_file_no_file(self) -> None:
        """Test the main program with pull, but no purpose.  We're not testing the
        actual details of the invocation, just that it's invoked."""
        config_file = self._setup_config(_mk_templates([], []))
        res = main.main(['main.py', '-C', config_file, '--document-type', 'discovery-map', 'push'])
        self.assertEqual(9, res)

    def test_main__pull_file_no_file(self) -> None:
        """Test the main program with pull, but no purpose.  We're not testing the
        actual details of the invocation, just that it's invoked."""
        config_file = self._setup_config(_mk_templates([], []))
        try:
            main.main(['main.py', '-C', config_file, '--document-type', 'discovery-map', 'pull'])
            self.fail('Did not raise an error')  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertIsNotNone(
                re.compile(
                    r"ExtensionPointRuntimeError\('data_store: Failed running fetch "
                    r"discovery-map - exited with 2'\)"
                ).match(repr(err))
            )

    def test_main__list_template(self) -> None:
        """Test the main program with template list."""
        config_file = self._setup_config(_mk_templates([], []))
        try:
            main.main(['main.py', '-C', config_file, 'list'])
            self.fail('Did not raise an error')  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertIsNotNone(
                re.compile(
                    r"^ExtensionPointRuntimeError\('data_store: Failed running fetch "
                    r"templates - exited with \d'\)$"
                ).match(repr(err))
            )

    def _setup_config(self, fetched_contents: Dict[str, Any]) -> str:
        config_file = os.path.join(self._temp_dir, 'config.ini')
        out = os.path.join(self._temp_dir, '{0}-src.json'.format(self._file_index))
        self._file_index += 1
        with open(out, 'w') as f:
            json.dump(fetched_contents, f)
        command = list(self._runnable)
        command.append('0')
        command.append(out)
        contents = (
            '[default]\n'
            'DATA_STORE_EXEC = ' + ' '.join(command) + '\n'
            'CACHE_DIR = ' + self._temp_dir + '\n'
        )
        with open(config_file, 'w') as f:
            f.write(contents)
        return config_file


def _mk_templates(
        gateways: List[Dict[str, Any]], services: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        'schema-version': 'v1',
        'document-version': '1',
        'gateway-templates': gateways,
        'service-templates': services,
    }
