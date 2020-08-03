
"""
Test the main module.
"""

import unittest
import os
import tempfile
import shutil
import platform
from .. import main, config, generate


class MainTest(unittest.TestCase):
    """Test the main function."""

    def setUp(self) -> None:
        self._orig_env = dict(os.environ)
        self._temp_dir = tempfile.mkdtemp()
        self._stop_file = os.path.join(self._temp_dir, 'stop.txt')
        os.environ[config.ENV__REFRESH_TIME] = '0.01'
        os.environ[config.ENV__FAILURE_SLEEP] = '0.01'
        os.environ[config.ENV__TRIGGER_STOP_FILE] = self._stop_file
        cmd = 'where' if platform.system() == 'Windows' else 'echo'
        os.environ[config.ENV__DATA_STORE_EXEC] = cmd
        os.environ[config.ENV__DISCOVERY_MAP_EXEC] = cmd
        os.environ[config.ENV__TEMP_DIR] = self._temp_dir
        os.environ['TEST.MODE'] = 'is active'

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._orig_env)
        shutil.rmtree(self._temp_dir)

    def test_main__one_pass__no_error(self) -> None:
        """Run one loop of the main program."""
        generate.MockGenerateData.PASSES_BEFORE_EXIT_CREATION = 1
        generate.MockGenerateData.RETURN_CODE = 0

        self.assertFalse(os.path.exists(self._stop_file))

        self.assertEqual(0, main.main(['main.py']))

        self.assertTrue(os.path.exists(self._stop_file))

    def test_main__stop_on_error(self) -> None:
        """Run one loop of the main program."""
        generate.MockGenerateData.PASSES_BEFORE_EXIT_CREATION = 2
        generate.MockGenerateData.RETURN_CODE = 21

        self.assertFalse(os.path.exists(self._stop_file))
        os.environ[config.ENV__EXIT_ON_GENERATION_FAILURE] = 'yes'

        self.assertEqual(21, main.main(['main.py']))

        self.assertFalse(os.path.exists(self._stop_file))

    def test_main__dont_stop_on_error(self) -> None:
        """Run one loop of the main program."""
        generate.MockGenerateData.PASSES_BEFORE_EXIT_CREATION = 1
        generate.MockGenerateData.RETURN_CODE = 1

        self.assertFalse(os.path.exists(self._stop_file))
        os.environ[config.ENV__EXIT_ON_GENERATION_FAILURE] = 'no'

        self.assertEqual(0, main.main(['main.py']))

        self.assertTrue(os.path.exists(self._stop_file))
