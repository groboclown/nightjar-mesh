
"""Test the config module."""

import unittest
import os
import platform
import tempfile
import shutil
from .. import config


class ConfigTest(unittest.TestCase):
    """Tests the Config class and module functions."""

    def setUp(self) -> None:
        # self.maxDiff = None
        self._temp_dir = tempfile.mkdtemp()
        self._valid_cmd = 'where' if platform.system() == 'Windows' else 'echo'

    def tearDown(self) -> None:
        shutil.rmtree(self._temp_dir)

    def test_get_profile__no_file(self) -> None:
        """Test get_profile with no config file."""
        not_file = os.path.join(self._temp_dir, 'not a file!')
        self.assertFalse(os.path.isfile(not_file))
        ret = config.get_profile(not_file, 'x')
        self.assertEqual({}, ret)

    def test_get_profile__no_profile(self) -> None:
        """Test get_profile with no config file."""
        cfg_file = os.path.join(self._temp_dir, 'config.ini')
        with open(cfg_file, 'w') as f:
            f.write('[abc]\na = b')
        ret = config.get_profile(cfg_file, 'x')
        self.assertEqual({}, ret)

    def test_create_configuration__long(self) -> None:
        """Test the config creator with long-form arguments"""
        cfg_file = os.path.join(self._temp_dir, 'config.ini')
        with open(cfg_file, 'w') as f:
            f.write('[abc]\na = b\nDATA_STORE_EXEC = ' + self._valid_cmd + '\nCACHE_DIR = .\n')
        ret = config.create_configuration([
            '--config', cfg_file,
            '--profile', 'abc',
            '--document-type', 'other',
            '--file', 'x.txt',
            '--category', 'gateway',
            '--purpose', 'purp',
            '--namespace', 'n1',
            '--service', 's1',
            '--color', 'c1',
            'push',
        ])
        expected_env = dict(os.environ)
        expected_env.update({
            'A': 'b', 'DATA_STORE_EXEC': self._valid_cmd,
            'CACHE_DIR': '.',
        })
        self.assertEqual(expected_env, ret.config_env)
        self.assertEqual('other', ret.document_type)
        self.assertEqual('x.txt', ret.filename)
        self.assertEqual('gateway', ret.category)
        self.assertEqual('purp', ret.purpose)
        self.assertEqual('n1', ret.namespace)
        self.assertEqual('s1', ret.service)
        self.assertEqual('c1', ret.color)
        self.assertEqual('push', ret.action)

        cache_dir = ret.cache_dir
        self.assertEqual('.', cache_dir)
        self.assertTrue(os.path.isdir(cache_dir))
        del ret
        self.assertTrue(os.path.isdir(cache_dir))

    def test_create_configuration__minimal(self) -> None:
        """Test the config creator with long-form arguments"""
        cfg_file = os.path.join(self._temp_dir, 'config.ini')
        with open(cfg_file, 'w') as f:
            f.write('[abc]\nDATA_STORE_EXEC = ' + self._valid_cmd + '\n')
        ret = config.create_configuration([
            '--config', cfg_file,
            '--profile', 'abc',
            'push',
        ])
        cache_dir = ret.cache_dir
        expected_env = dict(os.environ)
        expected_env.update({'DATA_STORE_EXEC': self._valid_cmd})
        self.assertEqual(expected_env, ret.config_env)
        self.assertEqual('one-template', ret.document_type)
        self.assertEqual(None, ret.filename)
        self.assertEqual('', ret.category)
        self.assertEqual('', ret.purpose)
        self.assertEqual('default', ret.namespace)
        self.assertEqual('default', ret.service)
        self.assertEqual('default', ret.color)
        self.assertEqual('push', ret.action)

        self.assertTrue(os.path.isdir(cache_dir))
        del ret
        self.assertFalse(os.path.exists(cache_dir))
