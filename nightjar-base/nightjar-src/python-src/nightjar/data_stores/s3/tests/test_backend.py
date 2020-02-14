
from typing import List, Tuple, Optional, Any
import unittest
import datetime
import boto3
import io
import botocore.stub  # type: ignore
from .. import paths
from ..backend import (
    S3Backend,
    GatewayConfigEntity,
    ServiceColorTemplateEntity,
)
from ..config import (
    S3EnvConfig, ENV_BUCKET, ENV_BASE_PATH, AWS_REGION,
)


class S3BackendTest(unittest.TestCase):
    def test_get_client(self) -> None:
        config = S3EnvConfig()
        config.load({
            ENV_BUCKET: 's3bucket',
            ENV_BASE_PATH: '/p/a1/',
            AWS_REGION: 'eu-north-12',
        })
        bk = S3Backend(config)
        client = bk.get_client()
        self.assertIsNotNone(client)

    def test_get_active_version__none(self) -> None:
        s3 = MockS3()
        # TODO use paths to generate the path.
        s3.mk_list_entries('s3bucket', 'p/a2/version/act/', [])
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a2'}))
            bk.client = s3.client
            version = bk.get_active_version('act')
            self.assertEqual(version, 'first')

    def test_get_active_version__one(self) -> None:
        s3 = MockS3()
        # TODO use paths to generate the path.
        s3.mk_list_entries('s3bucket', 'p/a2/version/act/', [('a1', 100,)])
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a2'}))
            bk.client = s3.client
            version = bk.get_active_version('act')
            self.assertEqual(version, 'a1')

    def test_get_active_version__several(self) -> None:
        s3 = MockS3()
        # TODO use paths to generate the path.
        s3.mk_list_entries('s3bucket', 'p/a2/version/act/', [('a1', 100,), ('a2', 120,), ('a3', 5), ('a4', 10)])
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a2'}))
            bk.client = s3.client
            version = bk.get_active_version('act')
            self.assertEqual(version, 'a3')

    def test_download_service_color(self) -> None:
        s3 = MockS3()
        # TODO use paths to generate the path.
        s3.mk_download('s3bucket', 'p/a3/v1a/service/n1/s1/c1/p1', 'cc1')
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a3'}))
            bk.client = s3.client
            content = bk.download('v1a', ServiceColorTemplateEntity('n1', 's1', 'c1', 'p1'))
            self.assertEqual(content, 'cc1')

    def test_download_gateway(self) -> None:
        s3 = MockS3()
        # TODO use paths to generate the path.
        s3.mk_download('s3bucket', 'p/a4/1b/gateway/n1/public/p1.txt', 'cc1')
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a4'}))
            bk.client = s3.client
            content = bk.download('1b', GatewayConfigEntity('n1', True, 'p1.txt'))
            self.assertEqual(content, 'cc1')


class MockS3:
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
            self, bucket: str, prefix: str, keys: List[Tuple[str, Optional[int]]]
    ) -> None:
        resp = {'IsTruncated': False, 'Name': bucket, 'Prefix': prefix, 'KeyCount': len(keys)}
        # "Contents" is only given if there are > 0 keys.
        if keys:
            resp['Contents'] = [{
                'Key': prefix + key,
                # S3 always returns time with tz
                'LastModified': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(delta or 0),
                'Size': 100,
            } for key, delta in keys]

        self.stubber.add_response(
            'list_objects_v2', resp, dict(
                Bucket=bucket,
                Delimiter='/',
                EncodingType='url',
                Prefix=prefix,
                FetchOwner=False,
            )
        )

    def mk_download(self, bucket: str, key: str, content: str) -> None:
        # Note: this only works for small content sizes.
        bin_content = content.encode('utf-8')
        self.stubber.add_response(
            'head_object',
            {
                'ContentLength': len(bin_content)
            }, dict(
                Bucket=bucket,
                Key=key,
            )
        )
        self.stubber.add_response(
            'get_object',
            {
                'Body': io.BytesIO(bin_content),
            }, dict(
                Bucket=bucket,
                Key=key,
            )
        )
