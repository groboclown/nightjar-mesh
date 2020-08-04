
"""Test the s3 module."""

import unittest
import io
from botocore.exceptions import ClientError, ProfileNotFound  # type: ignore
from .s3_mock import MockS3
from .. import s3
from ..config import Config, ENV__BUCKET, DEFAULT_BASE_PATH


class S3Test(unittest.TestCase):  # pylint: disable=R0904
    """Tests for the s3 module functions."""

    def setUp(self) -> None:
        self.config = Config({'AWS_REGION': 'eu-north-99', ENV__BUCKET: 'my-bucket'})

    def test_get_client(self) -> None:
        """get client test"""
        s3.set_aws_config({})
        client = s3.get_s3_client()
        self.assertIsNotNone(client)

    def test_get_client_with_region(self) -> None:
        """Test getting a client with a region set."""
        s3.set_aws_config({'AWS_REGION': 'eu-north-9999'})
        client = s3.get_s3_client()
        self.assertIsNotNone(client)
        self.assertEqual('eu-north-9999', client.meta.region_name)

    def test_get_client_with_bad_profile(self) -> None:
        """Test getting a client with a profile set.  This ensures that
        the profile property is used."""
        s3.set_aws_config({'AWS_PROFILE': 'nightjar: not a real profile'})
        try:
            s3.get_s3_client()
            self.fail("Did not raise an exception")  # pragma no cover
        except ProfileNotFound as err:
            self.assertEqual(
                "ProfileNotFound('The config profile "
                "(nightjar: not a real profile) could not be found')",
                repr(err)
            )

    def test_request_requires_retry__yes(self) -> None:
        """Test the request_requires_retry function where it does require a retry."""
        # To best simulate this. use the s3 mock to raise the error.
        mock_s3 = MockS3()
        mock_s3.mk_download_head_throttled(self.config.bucket, 'a/b')
        with mock_s3:
            try:
                out = io.BytesIO()
                s3.get_s3_client().download_fileobj(self.config.bucket, 'a/b', out)
                self.fail('Did not raise an exception')  # pragma no cover
            except ClientError as err:
                res = s3.request_requires_retry(err)
                self.assertTrue(res)

    def test_request_requires_retry__no(self) -> None:
        """Test request_requires_retry where it doesn't require retry."""
        # To best simulate this. use the s3 mock to raise the error.
        mock_s3 = MockS3()
        mock_s3.mk_download_key_not_found(self.config.bucket, 'a/b')
        with mock_s3:
            try:
                out = io.BytesIO()
                s3.get_s3_client().download_fileobj(self.config.bucket, 'a/b', out)
                self.fail('Did not raise an exception')  # pragma no cover
            except ClientError as err:
                res = s3.request_requires_retry(err)
                self.assertFalse(res)

    def test_request_requires_retry__not_client_error(self) -> None:
        """Test request_requires_retry with a non-client error."""
        res = s3.request_requires_retry(Exception('foo'))
        self.assertFalse(res)

    def test_is_404_error__key_not_found(self) -> None:
        """Test is_404_error with a non-client error."""
        mock_s3 = MockS3()
        mock_s3.mk_download_key_not_found(self.config.bucket, 'a/b')
        with mock_s3:
            try:
                out = io.BytesIO()
                s3.get_s3_client().download_fileobj(self.config.bucket, 'a/b', out)
                self.fail('Did not raise an exception')  # pragma no cover
            except ClientError as err:
                res = s3.is_404_error(err)
                self.assertTrue(res)

    def test_is_404_error__404(self) -> None:
        """Test is_404_error with a non-client error."""
        mock_s3 = MockS3()
        mock_s3.mk_download_404(self.config.bucket, 'a/b')
        with mock_s3:
            try:
                out = io.BytesIO()
                s3.get_s3_client().download_fileobj(self.config.bucket, 'a/b', out)
                self.fail('Did not raise an exception')  # pragma no cover
            except ClientError as err:
                res = s3.is_404_error(err)
                self.assertTrue(res)

    def test_is_404_error__no(self) -> None:
        """Test is_404_error with a non-client error."""
        mock_s3 = MockS3()
        mock_s3.mk_download_head_throttled(self.config.bucket, 'a/b')
        with mock_s3:
            try:
                out = io.BytesIO()
                s3.get_s3_client().download_fileobj(self.config.bucket, 'a/b', out)
                self.fail('Did not raise an exception')  # pragma no cover
            except ClientError as err:
                res = s3.is_404_error(err)
                self.assertFalse(res)

    def test_is_404_error__not_client_error(self) -> None:
        """Test is_404_error with a non-client error."""
        res = s3.is_404_error(Exception('foo'))
        self.assertFalse(res)

    def test_delete_ok(self) -> None:
        """Test the delete function where everything goes fine."""
        mock_s3 = MockS3()
        mock_s3.mk_delete(self.config.bucket, ['a/b', 'c/d'])
        with mock_s3:
            s3.delete(self.config, ['a/b', 'c/d'])

    def test_delete_404(self) -> None:
        """Test the delete function where at least one of the keys isn't found."""
        mock_s3 = MockS3()
        mock_s3.mk_delete_404(self.config.bucket, ['a/b', 'c/d'])
        with mock_s3:
            s3.delete(self.config, ['a/b', 'c/d'])

    def test_delete_throttled(self) -> None:
        """Test the delete function where s3 requests it's done again."""
        mock_s3 = MockS3()
        mock_s3.mk_delete_throttled(self.config.bucket, ['a/b', 'c/d'])
        with mock_s3:
            s3.delete(self.config, ['a/b', 'c/d'])

    def test_delete_other(self) -> None:
        """Test the delete function some some other error."""
        mock_s3 = MockS3()
        mock_s3.mk_delete_access_denied(self.config.bucket, ['a/b', 'c/d'])
        with mock_s3:
            try:
                s3.delete(self.config, ['a/b', 'c/d'])
                self.fail("Did not raise an exception")  # pragma no cover
            except ClientError:
                # We're just checking that the exception was re-thrown.
                pass

    def test_delete_no_keys(self) -> None:
        """Test delete where no keys are requested"""
        # No delete should be requested...
        mock_s3 = MockS3()
        with mock_s3:
            s3.delete(self.config, [])

    def test_delete_too_many_keys(self) -> None:
        """Test delete with too many keys."""
        mock_s3 = MockS3()
        with mock_s3:
            # A bit of magic - turn the 'a' into 1000 characters,
            # then split that into a list of 1000 elements, each is 'a'.
            try:
                s3.delete(self.config, list('a' * 1001))
                self.fail("Did not raise an exception")  # pragma no cover
            except ValueError as err:
                self.assertEqual(
                    "ValueError('Cannot handle > 1000 paths right now.')",
                    repr(err)
                )

    def test_download_404(self) -> None:
        """Test download when the key doesn't exist."""
        mock_s3 = MockS3()
        mock_s3.mk_download_key_not_found(self.config.bucket, 'x/y/z')
        with mock_s3:
            res = s3.download(self.config, 'x/y/z')
            self.assertEqual(31, res)

    def test_download_retry(self) -> None:
        """Test download when a retry is returned."""
        mock_s3 = MockS3()
        mock_s3.mk_download_head_throttled(self.config.bucket, 'x/y/z')
        with mock_s3:
            res = s3.download(self.config, 'x/y/z')
            self.assertEqual(31, res)

    def test_download_other(self) -> None:
        """Test download when some other error is returned."""
        mock_s3 = MockS3()
        mock_s3.mk_download_head_access_denied(self.config.bucket, 'x/y/z')
        with mock_s3:
            try:
                s3.download(self.config, 'x/y/z')
                self.fail("Did not raise an exception")  # pragma no cover
            except ClientError as err:
                self.assertEqual(
                    "ClientError('An error occurred (AccessDenied) when "
                    "calling the HeadObject operation: ')",
                    repr(err),
                )

    def test_download_ok(self) -> None:
        """Test download when the key exists and the contents are ok."""
        mock_s3 = MockS3()
        mock_s3.mk_download(self.config.bucket, 'x/y/z', b'a-b-c')
        with mock_s3:
            res = s3.download(self.config, 'x/y/z')
            self.assertEqual(b'a-b-c', res)

    def test_upload_retry(self) -> None:
        """Test upload with a retry response."""
        mock_s3 = MockS3()
        mock_s3.mk_upload_throttled(self.config.bucket, 'x/y/z')
        with mock_s3:
            res = s3.upload(self.config, 'x/y/z', b'data')
            self.assertEqual(31, res)

    def test_upload_other(self) -> None:
        """Test upload with another error"""
        mock_s3 = MockS3()
        mock_s3.mk_upload_access_denied(self.config.bucket, 'x/y/z')
        with mock_s3:
            try:
                s3.upload(self.config, 'x/y/z', b'data')
                self.fail('Did not raise an exception')  # pragma no cover
            except ClientError as err:
                self.assertEqual(
                    "ClientError('An error occurred (AccessDenied) when "
                    "calling the PutObject operation: ')",
                    repr(err),
                )

    def test_upload(self) -> None:
        """Test upload with another error"""
        mock_s3 = MockS3()
        mock_s3.mk_upload(self.config.bucket, 'x/y/z', b'data')
        with mock_s3:
            res = s3.upload(self.config, 'x/y/z', b'data')
            self.assertEqual(0, res)

    def test_list_entries__empty(self) -> None:
        """Test list_entries with no keys."""
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, 'a/b', [])
        with mock_s3:
            res = list(s3.list_entries(self.config, 'a/b'))
            self.assertEqual([], res)

    def test_list_entries__one(self) -> None:
        """Test list entries with one response."""
        mock_s3 = MockS3()
        mock_s3.mk_list_entries(self.config.bucket, '1/2', [('foo', 0,)])
        with mock_s3:
            res = list(s3.list_entries(self.config, '1/2'))
            self.assertEqual(1, len(res))
            self.assertEqual('1/2/foo', res[0][0])

    def test_get_document_s3_path(self) -> None:
        """Test get_document_s3_path"""
        res = s3.get_document_s3_path(self.config, 'tuna')
        self.assertEqual('nightjar-datastore/tuna', res)

    def test_get_meta_file_s3_key(self) -> None:
        """Test get_meta_file_s3_key"""
        self.config.base_path = 'x/y'
        res = s3.get_meta_file_s3_key(self.config, 'tuna', 'melt')
        self.assertEqual('x/y/tuna/melt.meta', res)

    def test_get_version_file_s3_key(self) -> None:
        """Test get_version_file_s3_key"""
        res = s3.get_version_file_s3_key(self.config, 'tuna', 'ahi')
        self.assertEqual(DEFAULT_BASE_PATH + '/tuna/ahi.data', res)
