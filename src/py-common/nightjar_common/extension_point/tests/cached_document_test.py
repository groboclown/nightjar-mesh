
"""Tests the cached_document module."""

from typing import Dict, List, Any
import unittest
import os
import tempfile
import shutil
import json
from .. import cached_document
from .. import errors


class CachedDocumentTest(unittest.TestCase):
    """Tests the CachedDocument class"""

    def setUp(self) -> None:
        self._validation_stack: List[Dict[str, Any]] = []
        self._temp_dir = tempfile.mkdtemp()
        self.cached_file = os.path.join(self._temp_dir, 'cached')
        self.update_file = os.path.join(self._temp_dir, 'update')
        self.commit_file = os.path.join(self._temp_dir, 'commit')
        with open(self.commit_file, 'w') as f:
            f.write('boo')
        self.doc = cached_document.CachedDocument(
            'ext_1',
            'doc_1',
            self.cached_file,
            self.update_file,
            self.commit_file,
            self._validator,
            True,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self._temp_dir)

    def test_after_fetch__valid_file_no_error(self) -> None:
        """Ensure that the after_fetch method, with a valid update file and no error, is fine."""
        # Run the process twice.  Once to create the initial cache value, another to test
        # with an existing cache value.

        expected_1 = {"x": "y", cached_document.DOCUMENT_VERSION_KEY: "1"}
        expected_2 = {"x": "z", cached_document.DOCUMENT_VERSION_KEY: "2"}
        with open(self.update_file, 'w') as f:
            json.dump(expected_1, f)
        res = self.doc.after_fetch(0)
        self.assertEqual(expected_1, res)
        self.assertEqual(1, len(self._validation_stack))
        self.assertEqual(expected_1, self._validation_stack.pop())

        with open(self.update_file, 'w') as f:
            json.dump(expected_2, f)
        res = self.doc.after_fetch(0)
        self.assertEqual(expected_2, res)
        self.assertEqual(1, len(self._validation_stack))
        self.assertEqual(expected_2, self._validation_stack.pop())

    def test_after_fetch__valid_file_but_error(self) -> None:
        """Ensure that the after_fetch method, with a valid update file and no error, is fine."""
        # Run the process twice.  Once to create the initial cache value, another to test
        # with an existing cache value.

        expected_1 = {"x": "y", cached_document.DOCUMENT_VERSION_KEY: "1"}
        expected_2 = {"x": "z", cached_document.DOCUMENT_VERSION_KEY: "2"}
        with open(self.update_file, 'w') as f:
            json.dump(expected_1, f)
        res = self.doc.after_fetch(0)
        self.assertEqual(expected_1, res)
        self.assertEqual(1, len(self._validation_stack))
        self.assertEqual(expected_1, self._validation_stack.pop())

        with open(self.update_file, 'w') as f:
            json.dump(expected_2, f)
        res = self.doc.after_fetch(1)
        self.assertEqual(expected_1, res)
        self.assertEqual(0, len(self._validation_stack))
        self.assertFalse(os.path.isfile(self.update_file))

    def test_check_run_error__success(self) -> None:
        """Ensure check_run_error does the right thing."""
        self.doc.check_run_error(0, 'foo')

    def test_check_run_error__retry(self) -> None:
        """Ensure check_run_error does the right thing."""
        try:
            self.doc.check_run_error(31, 'foo')
            self.fail('did not raise exception')  # pragma no cover
        except errors.ExtensionPointTooManyRetries as err:
            self.assertEqual('ext_1', err.source)
            self.assertEqual('foo doc_1', err.action)

    def test_check_run_error__other(self) -> None:
        """Ensure check_run_error does the right thing."""
        try:
            self.doc.check_run_error(2, 'foo')
            self.fail('did not raise exception')  # pragma no cover
        except errors.ExtensionPointRuntimeError as err:
            self.assertEqual('ext_1', err.source)
            self.assertEqual('foo doc_1', err.action)
            self.assertEqual(2, err.exit_code)

    def _validator(self, val: Dict[str, Any]) -> Dict[str, Any]:
        self._validation_stack.append(val)
        return val
