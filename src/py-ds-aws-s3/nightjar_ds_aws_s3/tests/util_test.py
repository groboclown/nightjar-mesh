
"""Test the util module"""

import unittest
from .. import util


class UtilTest(unittest.TestCase):
    """Test the util functions"""
    def test_get_version_from_data_key_name__with_slash(self) -> None:
        """Test get_version_from_data_key_name for a path with a slash."""
        res = util.get_version_from_data_key_name('name/and/value' + util.DATA_FILE_EXTENSION)
        self.assertEqual('value', res)

    def test_is_meta_file__yes(self) -> None:
        """Test is_meta_file when it is one."""
        res = util.is_meta_file('a/b/c/d/foo' + util.META_FILE_EXTENSION)
        self.assertTrue(res)

    def test_is_meta_file__no(self) -> None:
        """Test is_meta_file when it is not one."""
        res = util.is_meta_file('a/b/c/d/foo.blah')
        self.assertFalse(res)
        res = util.is_meta_file('a/b/c/d/foo.blah' + util.DATA_FILE_EXTENSION)
        self.assertFalse(res)

    def test_is_data_file__yes(self) -> None:
        """Test is_data_file when it is one."""
        res = util.is_data_file('a/b/c/d/foo' + util.DATA_FILE_EXTENSION)
        self.assertTrue(res)

    def test_is_data_file__no(self) -> None:
        """Test is_data_file when it is not one."""
        res = util.is_data_file('a/b/c/d/foo.blah')
        self.assertFalse(res)
        res = util.is_data_file('a/b/c/d/foo.blah' + util.META_FILE_EXTENSION)
        self.assertFalse(res)
