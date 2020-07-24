
"""
Test the config module.
"""

import unittest
import os
import tempfile
import shutil
import platform
from nightjar_common.extension_point.exceptions import ConfigurationError
from .. import config


class ConfigTest(unittest.TestCase):
    """Test the config class and creator."""

    def setUp(self) -> None:
        self._orig_env = dict(os.environ)
        self._valid_cmd = 'where' if platform.system() == 'Windows' else 'echo'
        self._temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._orig_env)
        shutil.rmtree(self._temp_dir)

    def test_init_no_settings(self) -> None:
        """Run the configuration with no environment variables set."""
        try:
            config.Config({
                # ... just to make sure ...
                config.ENV__TEMP_DIR: self._temp_dir,
            })
            self.fail("Did not raise a configuration error.")  # pragma no cover
        except ConfigurationError as err:
            self.assertEqual(config.ENV__DATA_STORE_EXEC, err.source)
            self.assertEqual('environment variable not defined', err.problem)

    def test_init_bad_proxy_mode(self) -> None:
        """Run the configuration with no environment variables set."""
        cfg = config.Config({
            config.ENV__PROXY_MODE: 'blah',
            config.ENV__DATA_STORE_EXEC: self._valid_cmd,
            config.ENV__DISCOVERY_MAP_EXEC: self._valid_cmd,
            config.ENV__ENVOY_CMD: self._valid_cmd,
            config.ENV__TEMP_DIR: self._temp_dir,
        })
        self.assertEqual(
            config.DEFAULT_PROXY_MODE,
            cfg.proxy_mode,
        )
        self.assertEqual(self._temp_dir, cfg.temp_dir)
