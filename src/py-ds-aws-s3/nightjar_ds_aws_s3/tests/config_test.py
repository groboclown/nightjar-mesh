
"""Test the config module"""

import unittest
from .. import config


class ConfigTest(unittest.TestCase):
    """Tests for the S3 configuration class."""

    def test_get_historical_preserve_count__non_int(self) -> None:
        """Test get_historical_preserve_count with a non-int value"""
        res = config.get_historical_preserve_count({config.ENV__HISTORICAL_PRESERVE_COUNT: 'x'})
        self.assertEqual(res, config.DEFAULT_HISTORICAL_PRESERVE_COUNT)

    def test_get_historical_preserve_count__negative(self) -> None:
        """Test get_historical_preserve_count with a negative value"""
        res = config.get_historical_preserve_count({config.ENV__HISTORICAL_PRESERVE_COUNT: '-1'})
        self.assertEqual(res, config.MIN_HISTORICAL_PRESERVE_COUNT)

    def test_get_historical_preserve_count__valid(self) -> None:
        """Test get_historical_preserve_count with an int value"""
        res = config.get_historical_preserve_count({config.ENV__HISTORICAL_PRESERVE_COUNT: '100'})
        self.assertEqual(res, 100)

    def test_get_historical_preserve_count__default(self) -> None:
        """Test get_historical_preserve_count with no value set"""
        res = config.get_historical_preserve_count({})
        self.assertEqual(res, config.DEFAULT_HISTORICAL_PRESERVE_COUNT)

    def test_get_historical_preserve_seconds__non_int(self) -> None:
        """Test get_historical_preserve_seconds with a non-int value"""
        res = config.get_historical_preserve_seconds({config.ENV__HISTORICAL_PRESERVE_HOURS: 'x'})
        self.assertEqual(res, config.DEFAULT_HISTORICAL_PRESERVE_HOURS * 60.0 * 60.0)

    def test_get_historical_preserve_seconds__negative(self) -> None:
        """Test get_historical_preserve_seconds with a negative int value"""
        res = config.get_historical_preserve_seconds({config.ENV__HISTORICAL_PRESERVE_HOURS: '-1'})
        self.assertEqual(res, config.MIN_HISTORICAL_PRESERVE_HOURS * 60.0 * 60.0)

    def test_get_historical_preserve_seconds__valid(self) -> None:
        """Test get_historical_preserve_seconds with an int value"""
        res = config.get_historical_preserve_seconds({config.ENV__HISTORICAL_PRESERVE_HOURS: '100'})
        self.assertEqual(res, 100 * 60.0 * 60.0)

    def test_get_historical_preserve_seconds__default(self) -> None:
        """Test get_historical_preserve_seconds with no value set"""
        res = config.get_historical_preserve_seconds({})
        self.assertEqual(res, config.DEFAULT_HISTORICAL_PRESERVE_HOURS * 60.0 * 60.0)

    def test_get_max_document_bytes__non_int(self) -> None:
        """Test get_max_document_bytes with a non-int value"""
        res = config.get_max_document_bytes({config.ENV__MAX_DOCUMENT_SIZE_MB: 'x'})
        self.assertEqual(res, config.DEFAULT_MAX_DOCUMENT_SIZE_MB * 1024 * 1024)

    def test_get_max_document_bytes__negative(self) -> None:
        """Test get_max_document_bytes with a negative int value"""
        res = config.get_max_document_bytes({config.ENV__MAX_DOCUMENT_SIZE_MB: '-1'})
        self.assertEqual(res, config.MIN_DOCUMENT_SIZE_MB * 1024 * 1024)

    def test_get_max_document_bytes__min_size(self) -> None:
        """Test get_max_document_bytes with a negative int value"""
        res = config.get_max_document_bytes({config.ENV__MAX_DOCUMENT_SIZE_MB: '1'})
        self.assertEqual(res, config.MIN_DOCUMENT_SIZE_MB * 1024 * 1024)

    def test_get_max_document_bytes__valid(self) -> None:
        """Test get_max_document_bytes with an int value"""
        res = config.get_max_document_bytes({config.ENV__MAX_DOCUMENT_SIZE_MB: '100'})
        self.assertEqual(res, 100 * 1024 * 1024)

    def test_get_max_document_bytes__default(self) -> None:
        """Test get_max_document_bytes with no value set"""
        res = config.get_max_document_bytes({})
        self.assertEqual(res, config.DEFAULT_MAX_DOCUMENT_SIZE_MB * 1024 * 1024)

    def test_is_valid__yes(self) -> None:
        """Test a minimally valid config"""
        cfg = config.Config({config.ENV__BUCKET: 'abc'})
        res = cfg.is_valid()
        self.assertTrue(res)

    def test_is_valid__bucket_not_exist(self) -> None:
        """Test an invalid config, because the bucket is missing"""
        cfg = config.Config({})
        res = cfg.is_valid()
        self.assertFalse(res)

    def test_is_valid__bucket_with_slash(self) -> None:
        """Test an invalid config, because the bucket has a '/' in it."""
        cfg = config.Config({config.ENV__BUCKET: 'a/b'})
        res = cfg.is_valid()
        self.assertFalse(res)

    def test_get_path__no_extra_slashes(self) -> None:
        """Test split_key_to_path without prefix path"""
        cfg = config.Config({})
        cfg.base_path = 'a/b/c'
        res = cfg.get_path(['x', 'a'])
        self.assertEqual('a/b/c/x/a', res)

    def test_get_path__lots_of_slashes(self) -> None:
        """Test split_key_to_path without prefix path"""
        cfg = config.Config({})
        cfg.base_path = '//a/b/c//'
        res = cfg.get_path(['/x', '//a/////'])
        self.assertEqual('a/b/c/x/a', res)
