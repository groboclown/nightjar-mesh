
"""
Test the fetch module.
"""

import unittest
from .util import Local
from .. import fetch


class FetchTest(unittest.TestCase):
    """Test the fetch function."""

    def setUp(self) -> None:
        self._local = Local()

    def tearDown(self) -> None:
        self._local.tear_down()

    def test_templates_no_file(self) -> None:
        """Test that the function fails correctly if the template file doesn't exist."""
        self.assertFalse(self._local.does_template_exist())
        self.assertFalse(self._local.does_action_file_exist())
        res = fetch.fetch(self._local.config, 'templates', self._local.action_file, '')
        self.assertEqual(31, res)
        self.assertFalse(self._local.does_action_file_exist())

    def test_discovery_map_no_file(self) -> None:
        """Test that the function fails correctly if the discovery-map file doesn't exist."""
        self.assertFalse(self._local.does_config_exist())
        self.assertFalse(self._local.does_action_file_exist())
        res = fetch.fetch(self._local.config, 'discovery-map', self._local.action_file, '')
        self.assertEqual(31, res)
        self.assertFalse(self._local.does_action_file_exist())

    def test_previous_match(self) -> None:
        """Ensure that, when the previous version matches the requested previous version, the
        right exit code is returned with the action file not created."""
        self._local.write_template({'document-version': 'prev-1'})
        self.assertFalse(self._local.does_action_file_exist())
        res = fetch.fetch(self._local.config, 'templates', self._local.action_file, 'prev-1')
        self.assertEqual(30, res)
        self.assertFalse(self._local.does_action_file_exist())

    def test_not_previous_match(self) -> None:
        """Ensure that, when the previous version does not match the requested previous version,
        the right exit code is returned with the action file created."""
        self._local.write_template({'document-version': 'prev-1', 'expected-template': True})
        self.assertFalse(self._local.does_action_file_exist())
        res = fetch.fetch(self._local.config, 'templates', self._local.action_file, 'prev-2')
        self.assertEqual(0, res)
        self.assertEqual(
            {'document-version': 'prev-1', 'expected-template': True},
            self._local.read_action_file(),
        )

    def test_discovery_map_with_file(self) -> None:
        """Test that the function operates correctly if the discovery-map file exists."""
        self._local.write_config({'document-version': 'prev-1', 'expected-config': True})
        self.assertFalse(self._local.does_action_file_exist())
        res = fetch.fetch(self._local.config, 'discovery-map', self._local.action_file, '')
        self.assertEqual(0, res)
        self.assertEqual(
            {'document-version': 'prev-1', 'expected-config': True},
            self._local.read_action_file(),
        )
