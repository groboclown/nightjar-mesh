
"""Test the fetch module."""

import unittest
import datetime
import tempfile
import os
from .s3_mock import MockS3
from .. import fetch
from ..config import Config, ENV__BUCKET, ENV__BASE_PATH


class FetchTest(unittest.TestCase):
    """Test the fetch functions."""

    def setUp(self) -> None:
        self._orig_env = dict(os.environ)
        os.environ['DEBUG'] = 'true'
        self.config = Config({
            ENV__BUCKET: 'some-bucket',
            ENV__BASE_PATH: 'this/test',
            'AWS_REGION': 'us-east-1111',
        })
        self.outfile = tempfile.mktemp()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._orig_env)
        if os.path.isfile(self.outfile):
            os.unlink(self.outfile)

    def test_get_data_meta_entries__empty(self) -> None:
        """Test get_data_meta_entries with no entries."""
        data, meta = fetch.get_data_meta_entries([])
        self.assertEqual({}, data)
        self.assertEqual(set(), meta)

    def test_get_data_meta_entries__one_each(self) -> None:
        """Test get_data_meta_entries with one of each type of entry, not matching."""
        time0 = _mk_time(0)
        time1 = _mk_time(1000)
        data, meta = fetch.get_data_meta_entries([
            ('/1.data', time0),
            ('/2.meta', time1),
        ])
        self.assertEqual({'/1.data': time0}, data)
        self.assertEqual(set('2'), meta)

    def test_get_data_meta_entries__two_pairs(self) -> None:
        """Test get_data_meta_entries with two pairs of entries."""
        time0a = _mk_time(0)
        time0b = _mk_time(1)
        time1a = _mk_time(1000)
        time1b = _mk_time(1001)
        data, meta = fetch.get_data_meta_entries([
            ('/1.data', time0a),
            ('/1.meta', time0b),
            ('/2.data', time1a),
            ('/2.meta', time1b),
        ])
        self.assertEqual({'/1.data': time0a, '/2.data': time1a}, data)
        self.assertEqual({'2', '1'}, meta)

    def test_find_latest_data_version__empty(self) -> None:
        """Test find_latest_data_version with no entries."""
        data, version = fetch.find_latest_data_version({}, set())
        self.assertIsNone(data)
        self.assertEqual('', version)

    def test_find_latest_data_version__no_meta(self) -> None:
        """Test find_latest_data_version with no meta for the data."""
        time0 = _mk_time(0)
        data, version = fetch.find_latest_data_version({'x/y.data': time0}, set())
        self.assertIsNone(data)
        self.assertEqual('', version)

    def test_find_latest_data_version__one_data(self) -> None:
        """Test find_latest_data_version with no meta for the data."""
        time0 = _mk_time(0)
        data, version = fetch.find_latest_data_version({'x/y.data': time0}, set('y'))
        self.assertEqual(data, 'x/y.data')
        self.assertEqual('y', version)

    def test_find_latest_data_version__two_data(self) -> None:
        """Test find_latest_data_version with no meta for the data."""
        time0 = _mk_time(0)
        time1 = _mk_time(10)
        data, version = fetch.find_latest_data_version(
            {'x/y.data': time0, 'x/z.data': time1},
            {'y', 'z'},
        )
        self.assertEqual(data, 'x/y.data')
        self.assertEqual('y', version)

    def test_find_latest_data_version__two_data_reversed(self) -> None:
        """Test find_latest_data_version with no meta for the data."""
        time0 = _mk_time(0)
        time1 = _mk_time(10)
        data, version = fetch.find_latest_data_version(
            {'x/z.data': time1, 'x/y.data': time0},
            {'y', 'z'},
        )
        self.assertEqual(data, 'x/y.data')
        self.assertEqual('y', version)

    def test_find_top_data_entry__with_results(self) -> None:
        """Test find_top_data_entry with simple data set."""
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(
            self.config.bucket, self.config.base_path + '/doc',
            [
                ('abc.data', 2),
                ('abc.meta', 3),
                ('def.data', 10),
                ('def.meta', 11),
            ],
        )
        with mock_s3:
            res = fetch.find_top_data_entry(self.config, 'doc')
            self.assertEqual((self.config.base_path + '/doc/abc.data', 'abc'), res)

    def test_find_top_data_entry__with_no_results(self) -> None:
        """Test find_top_data_entry with simple data set."""
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, self.config.base_path + '/doc', [])
        with mock_s3:
            res = fetch.find_top_data_entry(self.config, 'doc')
            self.assertEqual(31, res)

    def test_fetch__no_data(self) -> None:
        """Test fetch with no existing document."""
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, self.config.base_path + '/doc', [])
        with mock_s3:
            res = fetch.fetch(self.config, 'doc', self.outfile, '')
            self.assertEqual(31, res)
            self.assertFalse(os.path.isfile(self.outfile))

    def test_fetch__same_version(self) -> None:
        """Test fetch with latest version is the same as requested."""
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, self.config.base_path + '/doc', [
            ('abc.data', 2),
            ('abc.meta', 3),
        ])
        with mock_s3:
            res = fetch.fetch(self.config, 'doc', self.outfile, 'abc')
            self.assertEqual(30, res)
            self.assertFalse(os.path.isfile(self.outfile))

    def test_fetch__failed_download(self) -> None:
        """Test fetch but the download fails."""
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, self.config.base_path + '/doc', [
            ('abc.data', 2),
            ('abc.meta', 3),
        ])
        mock_s3.mk_download_key_not_found(
            self.config.bucket, self.config.base_path + '/doc/abc.data',
        )
        with mock_s3:
            res = fetch.fetch(self.config, 'doc', self.outfile, '')
            self.assertEqual(31, res)
            self.assertFalse(os.path.isfile(self.outfile))

    def test_fetch__ok(self) -> None:
        """Test fetch with everything fine."""
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, self.config.base_path + '/doc', [
            ('abc.data', 2),
            ('abc.meta', 3),
        ])
        mock_s3.mk_download(
            self.config.bucket, self.config.base_path + '/doc/abc.data',
            b'my-contents',
        )
        with mock_s3:
            res = fetch.fetch(self.config, 'doc', self.outfile, '')
            self.assertEqual(0, res)

        self.assertTrue(os.path.isfile(self.outfile))
        with open(self.outfile, 'rb') as f:
            self.assertEqual(b'my-contents', f.read())


def _mk_time(delta: int) -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(delta)
