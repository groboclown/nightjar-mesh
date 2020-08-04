
"""
Test the main module.
"""

import unittest
import os
from .. import main


class MainTest(unittest.TestCase):
    """Test the main function."""

    def setUp(self) -> None:
        self._orig_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_main_no_args(self) -> None:
        """Run main with no arguments."""
        self.assertEqual(4, main.main(['main.py']))

    def test_main_bad_api_version(self) -> None:
        """Run main with a wrong api version."""
        self.assertEqual(4, main.main([
            'main.py', '--api-version=wrong',
            '--document=discovery-map',
            '--previous-document-version=',
            '--action=fetch',
            '--action-file=/blah',
        ]))

    def test_main_bad_action(self) -> None:
        """Run main with a wrong api version."""
        self.assertEqual(6, main.main([
            'main.py', '--api-version=1',
            '--document=discovery-map',
            '--previous-document-version=',
            '--action=wrong',
            '--action-file=/blah',
        ]))

    def test_main_commit(self) -> None:
        """Run main with a wrong api version."""
        os.environ['TEST.MODE'] = 'unit-test'
        self.assertEqual(12, main.main([
            'main.py', '--api-version=1',
            '--document=discovery-map',
            '--previous-document-version=',
            '--action=commit',
            '--action-file=/blah',
        ]))

    def test_main_fetch(self) -> None:
        """Run main with a wrong api version."""
        os.environ['TEST.MODE'] = 'unit-test'
        self.assertEqual(13, main.main([
            'main.py', '--api-version=1',
            '--document=discovery-map',
            '--previous-document-version=',
            '--action=fetch',
            '--action-file=/blah',
        ]))
