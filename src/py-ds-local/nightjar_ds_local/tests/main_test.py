
"""Tests for the main module."""

import unittest
import os
from .util import Local
from .. import main
from ..config import ENV_NAME__LOCAL_CONFIGURATION_FILE, ENV_NAME__LOCAL_TEMPLATE_FILE


class MainTest(unittest.TestCase):
    """Test the main function."""

    def setUp(self) -> None:
        self._local = Local()
        os.environ[ENV_NAME__LOCAL_TEMPLATE_FILE] = self._local.template_file
        os.environ[ENV_NAME__LOCAL_CONFIGURATION_FILE] = self._local.config_file

    def tearDown(self) -> None:
        self._local.tear_down()

    def test_no_arguments(self) -> None:
        """Ensure that, with no arguments given, it exits with exit code 1."""
        res = main.main(['main.py'])
        self.assertEqual(4, res)

    def test_invalid_version(self) -> None:
        """Ensure that, with no arguments given, it exits with exit code 1."""
        res = main.main(['main.py', "--api-version=abc"])
        self.assertEqual(4, res)

    def test_invalid_action(self) -> None:
        """Ensure the right exit code."""
        res = main.main([
            'main.py',
            "--api-version=1",
            "--action=wrong",
            "--activity=template",
            "--previous-document-version=",
            "--action-file=" + self._local.action_file,
        ])
        self.assertEqual(6, res)

    def test_invalid_commit_activity(self) -> None:
        """Ensure the right exit code."""
        self._create_action_file()
        self._create_basic_files()
        res = main.main([
            'main.py',
            "--api-version=1",
            "--action=commit",
            "--activity=wrong",
            "--previous-document-version=",
            "--action-file=" + self._local.action_file,
        ])
        self.assertEqual(5, res)

    def test_invalid_fetch_activity(self) -> None:
        """Ensure the right exit code."""
        self._create_basic_files()
        res = main.main([
            'main.py',
            "--api-version=1",
            "--action=fetch",
            "--activity=wrong",
            "--previous-document-version=",
            "--action-file=" + self._local.action_file,
        ])
        self.assertEqual(5, res)

    def _create_action_file(self) -> None:
        self._local.write_action_file({"type": "action"})

    def _create_basic_files(self) -> None:
        self._local.write_config({"type": "configurations"})
        self._local.write_template({"type": "templates"})
