
"""Data store backend for S3.

This is very simple.  This just stores the file with no history or anything.  Extremely simple
to make it easy to inspect and debug.
"""


from typing import Iterable, Dict, Tuple, List, Union, Any
import datetime
import io
import boto3
from botocore.config import Config as BotoConfig  # type: ignore
from botocore.exceptions import ClientError  # type: ignore

from .config import Config


def get_version_file_s3_key(config: Config, document_name: str, version: str) -> str:
    """Get the s3 entry key to the version file for the document."""
    return config.get_path([document_name, version + '.data'])


def get_meta_file_s3_key(config: Config, document_name: str, version: str) -> str:
    """Get the s3 entry key to the version file for the document."""
    return config.get_path([document_name, version + '.meta'])


def get_document_s3_path(config: Config, document_name: str) -> str:
    """Get the s3 entry key to the version file for the document."""
    return config.get_path([document_name])


def list_entries(config: Config, path: str) -> Iterable[Tuple[str, datetime.datetime]]:
    """List the entries in the path and get the time when they were updated.
    If an entry is too large (beyond max_document_bytes), then it is not returned.

    This performs an iterable from yield, so do not loop through the returned object
    multiple times."""
    # debug("Listing entries under {p}", p=path)
    paginator = get_s3_client().get_paginator('list_objects_v2')
    response_iterator = paginator.paginate(
        Bucket=config.bucket,
        EncodingType='url',
        Prefix=path,
        FetchOwner=False,
    )
    for page in response_iterator:
        if 'Contents' not in page:
            continue
        for info in page['Contents']:
            key = info.get('Key', '')
            modified = info.get('LastModified', None)
            if key and modified and info.get('Size', 0) <= config.max_document_bytes:
                yield key, modified


def upload(config: Config, path: str, contents: bytes) -> int:
    """Upload the contents to the path S3 key, in the bucket defined by the
    config.  The path should already have the prefix added to it."""
    assert len(contents) <= config.max_document_bytes
    # Note that the path argument musn't start with a '/', but the path construction
    # should handle this.
    print("[nightjar-ds-aws-s3] Uploading {0}".format(path))
    inp = io.BytesIO(contents)
    try:
        get_s3_client().upload_fileobj(inp, config.bucket, path)
        return 0
    except ClientError as err:
        # 404 errors may happen if the bucket doesn't exist,
        # and if that happens, it's not recoverable.
        if request_requires_retry(err):
            print("[nightjar-ds-aws-s3] Upload generated a retry request from S3: " + repr(err))
            return 31
        raise err


def download(config: Config, path: str) -> Union[bytes, int]:
    """Download the contents of the s3 key.  The path should already have
    the prefix added to it.  This returns a number on error, and a string
    on success."""
    # Note that the path argument musn't start with a '/', but the path construction
    # should handle this.
    out = io.BytesIO()
    try:
        get_s3_client().download_fileobj(config.bucket, path, out)
    except ClientError as err:
        if is_404_error(err):
            # File disappeared underneath us.
            print(
                "[nightjar-ds-aws-s3] Download generated a not-found response from S3: " + repr(err)
            )
            return 31
        if request_requires_retry(err):
            print("[nightjar-ds-aws-s3] Download generated a retry request from S3: " + repr(err))
            return 31
        raise err
    return out.getvalue()


def delete(config: Config, keys: List[str]) -> None:
    """Delete the listed keys"""
    if len(keys) <= 0:
        return
    if len(keys) > 1000:
        raise ValueError("Cannot handle > 1000 paths right now.")
    try:
        get_s3_client().delete_objects(
            Bucket=config.bucket,
            Delete={
                'Objects': [{'Key': p} for p in keys],
            }
        )
    except ClientError as err:
        if is_404_error(err):
            print(
                "[nightjar-ds-aws-s3] Attempted to delete at least one "
                "non-existent S3 key: {0}".format(keys)
            )
            return
        if request_requires_retry(err):
            # Ignore these in context of the s3 use-case for delete.
            # But it leaves a mess...
            print(
                "[nightjar-ds-aws-s3] Attempted to delete keys ({0}), "
                "but S3 told us to retry.  Won't retry.  Error: {1}".format(keys, repr(err))
            )
            return
        raise err


def is_404_error(err: Exception) -> bool:
    """Is this a not-found error?"""
    if isinstance(err, ClientError):
        # Generally this is just "NoSuchKey" we're looking for.
        # Note that when deleting, the "Message" part is "Not Found",
        # because the message is the human-readable English text.
        code = str(err.response.get('Error', {}).get('Code', 'x'))
        return code == '404' or code.lower() == 'nosuchkey'
    return False


def request_requires_retry(err: Exception) -> bool:
    """Does the error mean that a retry should be performed?"""
    if not isinstance(err, ClientError):
        return False
    code = err.response.get('Error', {}).get('Code', '').lower()
    message = err.response.get('Error', {}).get('Message', '')
    # This covers:
    #   ExpiredToken
    #   OperationAborted
    #   RequestTimeout
    #   SlowDown
    #   Busy
    #   RequestLimitExceeded
    # It might need to cover these, but it doesn't.
    #   RestoreAlreadyInProgress
    m_low = message.lower()
    if (
            'exceeded' in m_low or 'exceeded' in code
            or 'expire' in m_low or 'expire' in code
            or 'aborted' in m_low or 'aborted' in code
            or 'timeout' in m_low or 'timeout' in code
            or 'slow' in m_low or 'slow' in code
            or 'busy' in m_low or 'busy' in code
    ):
        print(
            "[nightjar-ds-aws-s3] Reporting error {message} as requiring a retry".format(
                message=message,
            )
        )
        return True
    return False


# ---------------------------------------------------------------------------
CLIENTS: Dict[str, object] = {}
CONFIG: Dict[str, str] = {}


def set_aws_config(config: Dict[str, str]) -> None:
    """Set the global AWS configuration."""
    CONFIG.clear()
    CLIENTS.clear()
    CONFIG.update(config)


def get_s3_client() -> Any:
    """Get the boto3 s3 client."""
    client_name = 's3'
    if client_name not in CLIENTS:
        session = get_session()
        CLIENTS[client_name] = session.client(client_name, config=BotoConfig(
            max_pool_connections=1,
            retries=dict(max_attempts=2)
        ))
    return CLIENTS[client_name]


def get_session() -> boto3.session.Session:
    """Create the AWS session for ECS clients."""
    region = CONFIG.get('AWS_REGION', None)
    profile = CONFIG.get('AWS_PROFILE', None)
    params: Dict[str, str] = {}
    if region:
        params['region_name'] = region
    if profile:
        params['profile_name'] = profile
    return boto3.session.Session(**params)  # type: ignore
