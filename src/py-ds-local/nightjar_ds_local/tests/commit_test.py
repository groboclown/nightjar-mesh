
"""
Test the commit module.
"""

from typing import cast
import unittest
import re
from .util import Local
from .. import commit


ISO_DATETIME_FORMAT_RE = re.compile(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+')


class CommitTest(unittest.TestCase):
    """Test the commit function."""

    def setUp(self) -> None:
        self._local = Local()

    def tearDown(self) -> None:
        self._local.tear_down()

    def test_template_no_source_file(self) -> None:
        """Test that the function fails correctly if the source file doesn't exist."""
        self.assertFalse(self._local.does_template_exist())
        self.assertFalse(self._local.does_action_file_exist())
        res = commit.commit(self._local.config, 'template', self._local.action_file)
        self.assertEqual(1, res)
        self.assertFalse(self._local.does_action_file_exist())
        self.assertFalse(self._local.does_template_exist())

    def test_configuration_no_source_file(self) -> None:
        """Test that the function fails correctly if the source file doesn't exist."""
        self.assertFalse(self._local.does_config_exist())
        self.assertFalse(self._local.does_action_file_exist())
        res = commit.commit(self._local.config, 'configuration', self._local.action_file)
        self.assertEqual(1, res)
        self.assertFalse(self._local.does_action_file_exist())
        self.assertFalse(self._local.does_config_exist())

    def test_configuration_with_file(self) -> None:
        """Test that the function operates correctly if the source file exists."""
        self._local.write_action_file({'expected-config': True})
        self.assertFalse(self._local.does_config_exist())
        self.assertFalse(self._local.does_template_exist())
        res = commit.commit(self._local.config, 'configuration', self._local.action_file)
        self.assertEqual(0, res)
        self.assertTrue(self._local.does_config_exist())
        self.assertFalse(self._local.does_template_exist())
        data = self._local.read_config()
        self.assertIsInstance(data, dict)
        self.assertIs(True, data.get('expected-config'))
        # print(data.get('commit-version'))
        self.assertIsNotNone(ISO_DATETIME_FORMAT_RE.match(
            cast(str, data.get('commit-version'))
        ))

    def test_template_with_file(self) -> None:
        """Test that the function operates correctly if the source file exists."""
        self._local.write_action_file({'expected-template': True})
        self.assertFalse(self._local.does_config_exist())
        self.assertFalse(self._local.does_template_exist())
        res = commit.commit(self._local.config, 'template', self._local.action_file)
        self.assertEqual(0, res)
        self.assertFalse(self._local.does_config_exist())
        self.assertTrue(self._local.does_template_exist())
        data = self._local.read_template()
        self.assertIsInstance(data, dict)
        self.assertIs(True, data.get('expected-template'))
        # print(data.get('commit-version'))
        self.assertIsNotNone(ISO_DATETIME_FORMAT_RE.match(
            cast(str, data.get('commit-version'))
        ))
