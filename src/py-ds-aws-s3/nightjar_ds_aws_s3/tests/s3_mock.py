
"""
Mock the S3 callouts
"""

from typing import List, Tuple, Optional, Union, Any
import io
import re
import datetime
import boto3
import botocore.stub  # type: ignore
from .. import s3


class MockS3:
    """Mock S3 client."""
    __slots__ = ('client', '_stub_client', 'stubber')

    def __init__(self) -> None:
        self.client: Any = None
        self._stub_client = boto3.client('s3')
        self.stubber = botocore.stub.Stubber(self._stub_client)

    def __enter__(self) -> None:
        self.client = self._stub_client
        s3.CLIENTS['s3'] = self._stub_client
        self.stubber.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self.client = None
        del s3.CLIENTS['s3']
        self.stubber.__exit__(exc_type, exc_val, exc_tb)

    def mk_list_entries(
            self, bucket: str, prefix: str, keys: List[Tuple[str, Optional[int]]],
    ) -> None:
        """Add list entries to the mock."""
        resp = {'IsTruncated': False, 'Name': bucket, 'Prefix': prefix, 'KeyCount': len(keys)}
        # "Contents" is only given if there are > 0 keys.
        if keys:
            resp['Contents'] = [{
                'Key': prefix + '/' + key,
                # S3 always returns time with tz
                'LastModified': (
                    datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(hours=delta or 0)
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

    def mk_download(self, bucket: str, key: str, bin_content: bytes) -> None:
        """Add downloadable content to the mock."""
        # Note: this only works for small content sizes.  Bigger than that has other
        # paging and so on mechanisms.
        self.stubber.add_response(
            'head_object', {
                'ContentLength': len(bin_content),
            }, dict(
                Bucket=bucket,
                Key=key,
            ),
        )
        self.stubber.add_response(
            'get_object', {
                'Body': io.BytesIO(bin_content),
            }, dict(
                Bucket=bucket,
                Key=key,
            ),
        )

    def mk_delete(self, bucket: str, keys: List[str]) -> None:
        """Delete a key."""
        self.stubber.add_response(
            'delete_objects', {}, dict(
                Bucket=bucket,
                Delete={'Objects': [{'Key': key} for key in keys]},
            ),
        )

    def mk_upload(
            self, bucket: str, key: Union[re.Pattern, str], contents: Optional[bytes],
    ) -> None:
        """Upload a value."""
        self.stubber.add_response(
            'put_object',
            {},
            dict(
                Body=botocore.stub.ANY if contents is None else ExpectedBinStream(contents),
                Bucket=bucket,
                Key=ExpectedMatcher(key) if isinstance(key, re.Pattern) else key,
            ),
        )

    def mk_download_key_not_found(self, bucket: str, key: str) -> None:
        """Add a key-not-found response"""
        self.stubber.add_client_error(
            'head_object',
            expected_params=dict(Bucket=bucket, Key=key),
            service_error_code='NoSuchKey',
        )

    def mk_download_404(self, bucket: str, key: str) -> None:
        """Add a key-not-found response"""
        self.stubber.add_client_error(
            'head_object',
            expected_params=dict(Bucket=bucket, Key=key),
            service_error_meta={'Code': '404', 'Message': 'Not Found'},
        )

    def mk_download_head_throttled(self, bucket: str, key: str) -> None:
        """Add a service-instance-not-found response"""
        self.stubber.add_client_error(
            'head_object',
            expected_params=dict(Bucket=bucket, Key=key),
            service_error_code='RequestTimeout',
        )

    def mk_download_head_access_denied(self, bucket: str, key: str) -> None:
        """Add a access error response"""
        self.stubber.add_client_error(
            'head_object',
            expected_params=dict(Bucket=bucket, Key=key),
            service_error_code='AccessDenied',
        )

    # Not used... Should it ever be used?
    # def mk_list_entries_throttled(self, bucket: str, prefix: str) -> None:
    #     """Add a throttle error response."""
    #     self.stubber.add_client_error(
    #         'list_objects_v2',
    #         expected_params=dict(
    #             Bucket=bucket,
    #             EncodingType='url',
    #             Prefix=prefix,
    #             FetchOwner=False,
    #         ),
    #         service_error_code='ExpiredToken',
    #     )

    def mk_delete_404(self, bucket: str, keys: List[str]) -> None:
        """Add a 404 response"""
        self.stubber.add_client_error(
            'delete_objects',
            expected_params=dict(
                Bucket=bucket,
                Delete={'Objects': [{'Key': key} for key in keys]},
            ),
            service_error_meta={'Code': '404', 'Message': 'Not Found'},
        )

    def mk_delete_throttled(self, bucket: str, keys: List[str]) -> None:
        """Add a request timed out response"""
        self.stubber.add_client_error(
            'delete_objects',
            expected_params=dict(
                Bucket=bucket,
                Delete={'Objects': [{'Key': key} for key in keys]},
            ),
            service_error_code='RequestTimeout',
        )

    def mk_delete_access_denied(self, bucket: str, keys: List[str]) -> None:
        """Add a access error response"""
        self.stubber.add_client_error(
            'delete_objects',
            expected_params=dict(
                Bucket=bucket,
                Delete={'Objects': [{'Key': key} for key in keys]},
            ),
            service_error_code='AccessDenied',
        )

    def mk_upload_throttled(self, bucket: str, key: Union[re.Pattern, str]) -> None:
        """Add a throttle error response."""
        self.stubber.add_client_error(
            'put_object',
            expected_params=dict(
                Body=botocore.stub.ANY,
                Bucket=bucket,
                Key=ExpectedMatcher(key) if isinstance(key, re.Pattern) else key,
            ),
            service_error_code='ExpiredToken',
        )

    def mk_upload_access_denied(self, bucket: str, path: str) -> None:
        """Add a throttle error response."""
        self.stubber.add_client_error(
            'put_object',
            expected_params=dict(
                Body=botocore.stub.ANY,
                Bucket=bucket,
                Key=path,
            ),
            service_error_code='AccessDenied',
        )


class ExpectedBinStream:
    """Expect a binary stream value."""
    def __init__(self, contents: bytes) -> None:
        self.contents = contents

    def __eq__(self, other: Any) -> bool:
        assert hasattr(other, 'read') and callable(other.read)
        data = bytes(other.read())
        return self.contents == data

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        # This is for if something fails, so good situations don't run it.
        return repr(self.contents)  # pragma no cover


class ExpectedMatcher:
    """Expect a string to match a regular expression."""
    def __init__(self, pattern: re.Pattern) -> None:
        self.pattern = pattern

    def __eq__(self, other: Any) -> bool:
        return self.pattern.match(str(other)) is not None

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        # This is for if something fails, so good situations don't run it.
        return repr(self.pattern)  # pragma no cover
