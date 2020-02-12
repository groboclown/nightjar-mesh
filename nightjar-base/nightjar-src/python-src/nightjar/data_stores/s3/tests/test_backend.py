
from typing import List, Tuple, Optional, Any
import unittest
import datetime
import boto3
import io
import botocore.stub  # type: ignore
from ..backend import (
    S3Backend, ServiceColorEntity, NamespaceEntity, get_entity_path,
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
        s3.mk_list_entries('s3bucket', 'p/a2/version/act/', [])
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a2'}))
            bk.client = s3.client
            version = bk.get_active_version('act')
            self.assertEqual(version, 'first')

    def test_get_active_version__one(self) -> None:
        s3 = MockS3()
        s3.mk_list_entries('s3bucket', 'p/a2/version/act/', [('a1', 100,)])
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a2'}))
            bk.client = s3.client
            version = bk.get_active_version('act')
            self.assertEqual(version, 'act/a1')

    def test_get_active_version__several(self) -> None:
        s3 = MockS3()
        s3.mk_list_entries('s3bucket', 'p/a2/version/act/', [('a1', 100,), ('a2', 120,), ('a3', 5), ('a4', 10)])
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a2'}))
            bk.client = s3.client
            version = bk.get_active_version('act')
            self.assertEqual(version, 'act/a3')

    def test_mk_path_service_color(self) -> None:
        # Default service and color, template
        self.assertEqual(
            get_entity_path('abc', ServiceColorEntity(None, None, 'p1.yaml', True)),
            'abc/service/__default__/__default__/template/p1.yaml',
        )

        # Default service and color, not template
        self.assertEqual(
            get_entity_path('1234', ServiceColorEntity(None, None, 'p2', False)),
            '1234/service/__default__/__default__/extracted/p2',
        )

        # Default color, template
        self.assertEqual(
            get_entity_path('qwerty', ServiceColorEntity('block', None, 'p3.txt', True)),
            'qwerty/service/block/__default__/template/p3.txt',
        )

        # Default color, not template
        self.assertEqual(
            get_entity_path('1234', ServiceColorEntity('chain', None, 'p2', False)),
            '1234/service/chain/__default__/extracted/p2',
        )

        # template
        self.assertEqual(
            get_entity_path('qwerty', ServiceColorEntity('foo', 'bar', 'p4.json', True)),
            'qwerty/service/foo/bar/template/p4.json',
        )

        # not template
        self.assertEqual(
            get_entity_path('1234', ServiceColorEntity('tuna', 'melt', 'p5', False)),
            '1234/service/tuna/melt/extracted/p5',
        )

    def test_mk_path_namespace(self) -> None:
        # Default namespace, template
        self.assertEqual(
            get_entity_path('abc', NamespaceEntity(None, 'p1.yaml', True)),
            'abc/namespace/__default__/template/p1.yaml',
        )

        # Default service and color, not template
        self.assertEqual(
            get_entity_path('1234', NamespaceEntity(None, 'p2', False)),
            '1234/namespace/__default__/extracted/p2',
        )

        # template
        self.assertEqual(
            get_entity_path('qwerty', NamespaceEntity('foo', 'p4.json', True)),
            'qwerty/namespace/foo/template/p4.json',
        )

        # not template
        self.assertEqual(
            get_entity_path('1234', NamespaceEntity('melt', 'p5', False)),
            '1234/namespace/melt/extracted/p5',
        )

    def test_download_service_color(self) -> None:
        s3 = MockS3()
        s3.mk_download('s3bucket', 'p/a3/v1a/service/s1/c1/template/p1', 'cc1')
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a3'}))
            bk.client = s3.client
            content = bk.download('v1a', ServiceColorEntity('s1', 'c1', 'p1', True))
            self.assertEqual(content, 'cc1')

    def test_download_namespace(self) -> None:
        s3 = MockS3()
        s3.mk_download('s3bucket', 'p/a4/1b/namespace/n1/extracted/p1.txt', 'cc1')
        with s3:
            bk = S3Backend(S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: 'p/a4'}))
            bk.client = s3.client
            content = bk.download('1b', NamespaceEntity('n1', 'p1.txt', False))
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
