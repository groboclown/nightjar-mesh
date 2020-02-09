
from typing import Iterable, Sequence, Optional, Any
import io
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from .config import S3EnvConfig

DEFAULT_SERVICE_NAME = '__default__'
DEFAULT_COLOR_NAME = '__default__'
MAX_CONTENT_SIZE = 4 * 1024 * 1024  # 4 MB


class S3Backend:
    def __init__(self, config: S3EnvConfig) -> None:
        self.config = config
        self.client = None

    def get_client(self) -> Any:
        if not self.client:
            region = self.config.aws_region
            profile = self.config.aws_profile
            session = boto3.session.Session(
                region_name=region,
                profile_name=profile,
            )
            self.client = session.client('servicediscovery', config=Config(
                max_pool_connections=1,
                retries=dict(max_attempts=2)
            ))
        return self.client

    def list_entries(self, path: str) -> Iterable[str]:
        paginator = self.get_client().get_paginator('list_objects_v2')
        response_iterator = paginator.paginate(
            Bucket=self.config.bucket,
            Delimiter='/',
            EncodingType='url',
            Prefix=path,
            FetchOwner=False,
        )
        for page in response_iterator:
            for info in page['Contents']:
                key = info.get('Key', '')
                if key and info.get('Size', 0) < MAX_CONTENT_SIZE:
                    yield key

    def download(self, path: str) -> str:
        out = io.BytesIO()
        self.get_client().download_fileobj(self.config.bucket, path, out)
        return out.getvalue().decode('utf-8')

    def delete(self, paths: Sequence[str]) -> bool:
        if len(paths) <= 0:
            return True
        if len(paths) == 1:
            self.get_client().delete_object(
                Bucket=self.config.bucket,
                Key=paths[0],
            )
            return True
        self.get_client().delete_objects(
            Bucket=self.config.bucket,
            Delete={
                'Objects': [{'Key': p} for p in paths]
            }
        )

    def upload(self, path: str, contents: str) -> None:
        assert len(contents) < MAX_CONTENT_SIZE
        inp = io.BytesIO(contents.encode('utf-8'))
        self.get_client().upload_fileobj(inp, self.config.bucket, path)

    def get_namespace_path(self, namespace: str, *parts: str) -> str:
        """Path for the by-namespace store."""
        part_text = '/'.join(parts)
        if part_text:
            part_text = '/' + part_text
        return '{0}/namespaces/{1}{2}'.format(self.config.base_path, namespace, part_text)

    def get_service_color_path(self, service: Optional[str], color: Optional[str], *parts: str) -> str:
        # Ensure this is a valid request.
        assert not (service is None and color is not None)
        service_name = service or DEFAULT_SERVICE_NAME
        color_name = color or DEFAULT_COLOR_NAME
        part_text = '/'.join(parts)
        if part_text:
            part_text = '/' + part_text
        return '{0}/service_color/{1}/{2}{3}'.format(
            self.config.base_path,
            service_name, color_name, part_text
        )
