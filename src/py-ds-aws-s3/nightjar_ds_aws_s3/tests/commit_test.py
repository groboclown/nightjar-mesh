
"""Test the commit module."""

import unittest
import datetime
import tempfile
import os
import json
import re
from .s3_mock import MockS3
from .. import commit, util
from ..config import Config, ENV__BUCKET, ENV__BASE_PATH


class CommitTest(unittest.TestCase):
    """Test the commit functions."""

    def setUp(self) -> None:
        self.config = Config({
            ENV__BUCKET: 'some-bucket',
            ENV__BASE_PATH: 'this/test',
            'AWS_REGION': 'us-east-1111',
        })
        self.src_file = tempfile.mktemp()

    def tearDown(self) -> None:
        if os.path.isfile(self.src_file):
            os.unlink(self.src_file)

    def test_json_binary_dump(self) -> None:
        """Test the json_binary_dump function."""
        res = commit.json_binary_dump({'x': 'y'})
        self.assertEqual(b'{"x": "y"}', res)

    def test_filter_old_document_entries__no_entries(self) -> None:
        """Test filter_old_document_entries with no entries."""
        res = commit.filter_old_document_entries([])
        self.assertEqual([], res)

    def test_filter_old_document_entries__invalid_entries(self) -> None:
        """Test filter_old_document_entries with only non-expected data."""
        res = commit.filter_old_document_entries([
            ('a/b/c/foo.txt', _mk_time(0)),
            ('a/b/c/bar.md', _mk_time(0)),
        ])
        self.assertEqual([], res)

    def test_filter_old_document_entries__pairs(self) -> None:
        """Test filter_old_document_entries with pairs of valid data."""
        res = commit.filter_old_document_entries([
            ('a/b/c/foo.txt', _mk_time(0)),
            ('a/b/c/bar.md', _mk_time(0)),
            ('a/b/c/foo.data', _mk_time(0)),
            ('a/b/c/foo.meta', _mk_time(0)),
        ])
        self.assertEqual(
            sorted(['a/b/c/foo.data', 'a/b/c/foo.meta']),
            sorted(res),
        )

    def test_filter_old_document_entries__dangling_meta(self) -> None:
        """Test filter_old_document_entries with pairs of valid data."""
        res = commit.filter_old_document_entries([
            ('a/b/c/foo.txt', _mk_time(0)),
            ('a/b/c/bar.md', _mk_time(0)),
            ('bar.meta', _mk_time(0)),
        ])
        self.assertEqual(
            sorted(['bar.meta']),
            sorted(res),
        )

    def test_filter_old_document_entries__dangling_data_old(self) -> None:
        """Test filter_old_document_entries with pairs of valid data."""
        res = commit.filter_old_document_entries([
            ('a/b/c/foo.txt', _mk_time(0)),
            ('a/b/c/bar.md', _mk_time(0)),
            ('bar.data', _mk_time(commit.OLD_FILE_TIME_DAYS * 24 + 1)),
        ])
        self.assertEqual(
            sorted(['bar.data']),
            sorted(res),
        )

    def test_filter_old_document_entries__dangling_data_young(self) -> None:
        """Test filter_old_document_entries with pairs of valid data."""
        res = commit.filter_old_document_entries([
            ('a/b/c/foo.txt', _mk_time(0)),
            ('a/b/c/bar.md', _mk_time(0)),
            ('bar.data', _mk_time(commit.OLD_FILE_TIME_DAYS * 24 - 1)),
        ])
        self.assertEqual([], res)

    def test_create_document_metadata(self) -> None:
        """Test create_document_metadata"""
        meta, data = commit.create_document_metadata('doc-1', {"x": "y"})

        # These are, for all intents and purposes, random values.
        self.assertEqual(meta['document-version'], data[commit.DOCUMENT_VERSION_KEY])
        self.assertIsInstance(meta['document-version'], str)
        del meta['document-version']
        del data[commit.DOCUMENT_VERSION_KEY]

        self.assertIsInstance(meta['local-time'], str)
        del meta['local-time']

        self.assertEqual({"x": "y"}, data)
        self.assertEqual(
            {
                'document': 'doc-1',
                'bare-contents-md5': '4938caaf6122a668312c0fa64d01ab26',
                'bare-contents-size': 34,
            },
            meta,
        )

    def test_load_document_information__not_json(self) -> None:
        """Test load_document_information with a non-json formatted file"""
        with open(self.src_file, 'w') as f:
            f.write('{[')
        res = commit.load_document_information('doc1', self.src_file)
        self.assertEqual(1, res)

    def test_load_document_information__valid(self) -> None:
        """Test load_document_information with a valid file"""
        with open(self.src_file, 'w') as f:
            json.dump({"tuna": "fish"}, f)
        res = commit.load_document_information('doc1', self.src_file)
        self.assertNotIsInstance(res, int)
        assert not isinstance(res, int)  # mypy requirement
        version, metadata, data = res
        self.assertEqual(version, metadata['document-version'])
        self.assertEqual(version, data['document-version'])
        self.assertEqual(
            {'document-version': version, 'tuna': 'fish'},
            data,
        )
        self.assertEqual('doc1', metadata['document'])

    def test_commit__valid(self) -> None:
        """Test commit where everything goes right."""
        with open(self.src_file, 'w') as f:
            json.dump({'brownie': 'fudge'}, f)
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(
            self.config.bucket, self.config.base_path + '/doco-2',
            [
                ('to-ignore.txt', 0),
                ('to-remove.data', commit.OLD_FILE_TIME_DAYS * 24 + 1),
                ('to-keep.data', commit.OLD_FILE_TIME_DAYS * 24 - 1),
                ('foo-to-remove.data', 4),
                ('foo-to-remove.meta', 5),
            ],
        )
        # We can't predict the version ahead of time...
        mock_s3.mk_upload(self.config.bucket, re.compile(
            '^' + re.escape(self.config.base_path + '/doco-2/') + '.*?' +
            re.escape(util.DATA_FILE_EXTENSION) + '$'
        ), None)
        mock_s3.mk_upload(self.config.bucket, re.compile(
            '^' + re.escape(self.config.base_path + '/doco-2/') + '.*?' +
            re.escape(util.META_FILE_EXTENSION) + '$'
        ), None)
        mock_s3.mk_delete(
            self.config.bucket,
            [
                self.config.base_path + '/doco-2/to-remove.data',
                self.config.base_path + '/doco-2/foo-to-remove.data',
                self.config.base_path + '/doco-2/foo-to-remove.meta',
            ]
        )
        with mock_s3:
            res = commit.commit(self.config, 'doco-2', self.src_file)
            self.assertEqual(0, res)

    def test_commit__invalid_document_info(self) -> None:
        """Test commit where the file format is bad."""
        with open(self.src_file, 'w') as f:
            f.write('{[')
        res = commit.commit(self.config, 'doco-2', self.src_file)
        self.assertEqual(1, res)

    def test_commit__failed_upload_pt1(self) -> None:
        """Test commit where the first upload is a retry."""
        with open(self.src_file, 'w') as f:
            json.dump({'brownie': 'fudge'}, f)
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, self.config.base_path + '/doco-2', [])
        # We can't predict the version ahead of time...
        mock_s3.mk_upload_throttled(self.config.bucket, re.compile(
            '^' + re.escape(self.config.base_path + '/doco-2/') + '.*?' +
            re.escape(util.DATA_FILE_EXTENSION) + '$'
        ))
        with mock_s3:
            res = commit.commit(self.config, 'doco-2', self.src_file)
            self.assertEqual(31, res)

    def test_commit__failed_upload_pt2(self) -> None:
        """Test commit where the second upload is a retry."""
        with open(self.src_file, 'w') as f:
            json.dump({'brownie': 'fudge'}, f)
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, self.config.base_path + '/doco-2', [])
        # We can't predict the version ahead of time...
        mock_s3.mk_upload(self.config.bucket, re.compile(
            '^' + re.escape(self.config.base_path + '/doco-2/') + '.*?' +
            re.escape(util.DATA_FILE_EXTENSION) + '$'
        ), None)
        mock_s3.mk_upload_throttled(self.config.bucket, re.compile(
            '^' + re.escape(self.config.base_path + '/doco-2/') + '.*?' +
            re.escape(util.META_FILE_EXTENSION) + '$'
        ))
        with mock_s3:
            res = commit.commit(self.config, 'doco-2', self.src_file)
            self.assertEqual(31, res)


def _mk_time(delta: int) -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=delta)
