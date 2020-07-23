
"""Tests for the main module."""

import unittest
import os
import tempfile
import shutil
from .. import main


class MainTest(unittest.TestCase):
    """Test the main function."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._orig_template = main.LOCAL_TEMPLATE_FILE
        self._local_template = os.path.join(self._tmpdir, 'templates.json')
        main.LOCAL_TEMPLATE_FILE = self._local_template

        self._orig_configs = main.LOCAL_CONFIGURATION_FILE
        self._local_configs = os.path.join(self._tmpdir, 'templates.json')
        main.LOCAL_CONFIGURATION_FILE = self._local_configs

        self._action_file = os.path.join(self._tmpdir, 'action-file.json')

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir)

    def test_no_arguments(self) -> None:
        """Ensure that, with no arguments given, it exits with exit code 1."""
        res = main.main([])
        self.assertEqual(1, res)

    def test_invalid_action(self) -> None:
        """Ensure the right exit code."""
        res = main.main([
            "--action=wrong",
            "--activity=template",
            "--previous-document-version=",
            "--action-file=" + self._action_file,
        ])
        self.assertEqual(1, res)

    def test_invalid_activity(self) -> None:
        """Ensure the right exit code."""
        res = main.main([
            "--action=commit",
            "--activity=wrong",
            "--previous-document-version=",
            "--action-file=" + self._action_file,
        ])
        self.assertEqual(1, res)
