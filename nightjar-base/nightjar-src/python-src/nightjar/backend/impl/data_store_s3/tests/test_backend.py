
"""Test the backend module."""

from typing import List, Tuple, Optional, Any
import unittest
import datetime
import io
import boto3
import botocore.stub  # type: ignore
from ..backend import (
    S3Backend,
    GatewayConfigEntity,
    ServiceColorTemplateEntity,
)
from ..config import (
    S3EnvConfig, PARAM__AWS_REGION, PARAM__S3_BASE_PATH, PARAM__S3_BUCKET,
)
from ...data_store_util import wide
from ....api.data_store.abc_backend import ACTIVITY_PROXY_CONFIGURATION
from .....protect import PROTECTION_PUBLIC


class S3BackendTest(unittest.TestCase):
    """Tests for the S3Backend class."""
    def test_get_client(self) -> None:
        """get client test"""
        config = S3EnvConfig({
            PARAM__S3_BUCKET.name: 's3bucket',
            PARAM__S3_BASE_PATH.name: '/p/a1/',
            PARAM__AWS_REGION.name: 'eu-north-12',
        })
        backend = S3Backend(config)
        client = backend.get_client()
        self.assertIsNotNone(client)

    def test_get_active_version__none(self) -> None:
        """No active version."""
        mock_s3 = MockS3()
        config = S3EnvConfig({
            PARAM__S3_BUCKET.name: 's3bucket',
            PARAM__S3_BASE_PATH.name: 'p/a2',
            PARAM__AWS_REGION.name: 'z',
        })
        mock_s3.mk_list_entries(
            's3bucket',
            'p/a2/' + ('/'.join(wide.get_version_reference_prefix(ACTIVITY_PROXY_CONFIGURATION))),
            [],
        )
        with mock_s3:
            backend = S3Backend(config)
            backend.client = mock_s3.client
            version = backend.get_active_version(ACTIVITY_PROXY_CONFIGURATION)
            self.assertEqual(version, ACTIVITY_PROXY_CONFIGURATION + '-first')

    def test_get_active_version__one(self) -> None:
        """One active version."""
        mock_s3 = MockS3()
        config = S3EnvConfig({
            PARAM__S3_BUCKET.name: 's3bucket',
            PARAM__S3_BASE_PATH.name: 'p/a2',
            PARAM__AWS_REGION.name: 'z',
        })
        mock_s3.mk_list_entries(
            's3bucket',
            'p/a2/' + ('/'.join(wide.get_version_reference_prefix(ACTIVITY_PROXY_CONFIGURATION))),
            [('/a1', 100,)],
        )
        with mock_s3:
            backend = S3Backend(config)
            backend.client = mock_s3.client
            version = backend.get_active_version(ACTIVITY_PROXY_CONFIGURATION)
            self.assertEqual(version, 'a1')

    def test_get_active_version__several(self) -> None:
        """Several active versions."""
        mock_s3 = MockS3()
        config = S3EnvConfig({
            PARAM__S3_BUCKET.name: 's3bucket',
            PARAM__S3_BASE_PATH.name: 'p/a2',
            PARAM__AWS_REGION.name: 'z',
        })
        mock_s3.mk_list_entries(
            's3bucket',
            'p/a2/' + ('/'.join(wide.get_version_reference_prefix(ACTIVITY_PROXY_CONFIGURATION))),
            [('/a1', 100,), ('/a2', 120,), ('/a3', 5), ('/a4', 10)],
        )
        with mock_s3:
            backend = S3Backend(config)
            backend.client = mock_s3.client
            version = backend.get_active_version(ACTIVITY_PROXY_CONFIGURATION)
            self.assertEqual(version, 'a3')

    def test_download_service_color(self) -> None:
        """Download service color"""
        mock_s3 = MockS3()
        config = S3EnvConfig({
            PARAM__S3_BUCKET.name: 's3bucket',
            PARAM__S3_BASE_PATH.name: 'p/a3',
            PARAM__AWS_REGION.name: 'z',
        })
        expected_entity = ServiceColorTemplateEntity('n1', 's1', 'c1', 'p1')
        mock_s3.mk_download(
            's3bucket',
            'p/a3/' + ('/'.join(wide.get_service_color_template_path('v1a', expected_entity))),
            'cc1',
        )
        with mock_s3:
            backend = S3Backend(config)
            backend.client = mock_s3.client
            content = backend.download('v1a', expected_entity)
            self.assertEqual(content, 'cc1')

    def test_download_gateway(self) -> None:
        """Download gateway"""
        mock_s3 = MockS3()
        config = S3EnvConfig({
            PARAM__S3_BUCKET.name: 's3bucket',
            PARAM__S3_BASE_PATH.name: 'p/a4',
            PARAM__AWS_REGION.name: 'z',
        })
        expected_entity = GatewayConfigEntity('n2', PROTECTION_PUBLIC, 'p1.txt')
        mock_s3.mk_download(
            's3bucket',
            'p/a4/' + ('/'.join(wide.get_gateway_config_path('1b', expected_entity))),
            'cc2',
        )
        with mock_s3:
            backend = S3Backend(config)
            backend.client = mock_s3.client
            content = backend.download('1b', expected_entity)
            self.assertEqual(content, 'cc2')


class MockS3:
    """Mock S3 client."""
    client: Any

    def __init__(self) -> None:
        self.client = None
        self._client = boto3.client('s3')
        self.stubber = botocore.stub.Stubber(self._client)

    def __enter__(self) -> None:
        self.client = self._client
        return self.stubber.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self.client = None
        return self.stubber.__exit__(exc_type, exc_val, exc_tb)

    def mk_list_entries(
            self, bucket: str, prefix: str, keys: List[Tuple[str, Optional[int]]],
    ) -> None:
        """Add list entries to the mock."""
        resp = {'IsTruncated': False, 'Name': bucket, 'Prefix': prefix, 'KeyCount': len(keys)}
        # "Contents" is only given if there are > 0 keys.
        if keys:
            resp['Contents'] = [{
                'Key': prefix + key,
                # S3 always returns time with tz
                'LastModified': (
                    datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(delta or 0)
                ),
                'Size': 100,
            } for key, delta in keys]

        self.stubber.add_response(
            'list_objects_v2', resp, dict(
                Bucket=bucket,
                EncodingType='url',
                Prefix=prefix,
                FetchOwner=False,
            ),
        )

    def mk_download(self, bucket: str, key: str, content: str) -> None:
        """Add downloadable content to the mock."""
        # Note: this only works for small content sizes.
        bin_content = content.encode('utf-8')
        self.stubber.add_response(
            'head_object',
            {
                'ContentLength': len(bin_content),
            }, dict(
                Bucket=bucket,
                Key=key,
            ),
        )
        self.stubber.add_response(
            'get_object',
            {
                'Body': io.BytesIO(bin_content),
            }, dict(
                Bucket=bucket,
                Key=key,
            ),
        )
