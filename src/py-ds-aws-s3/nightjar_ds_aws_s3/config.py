
"""
S3 Configuration Parameters
"""

# This file must be clean of any boto3 or boto imports.  Likewise, it
# can't import anything that in turn imports those.

from typing import List, Dict
import os


ENV__BUCKET = 'NJ_DSS3_BUCKET'
ENV__BASE_PATH = 'NJ_DSS3_BASE_PATH'
DEFAULT_BASE_PATH = 'nightjar-datastore'
ENV__HISTORICAL_PRESERVE_COUNT = 'NJ_DSS3_HISTORICAL_PRESERVE_COUNT'
DEFAULT_HISTORICAL_PRESERVE_COUNT = 6
MIN_HISTORICAL_PRESERVE_COUNT = 2
ENV__HISTORICAL_PRESERVE_HOURS = 'NJ_DSS3_HISTORICAL_PRESERVE_HOURS'
DEFAULT_HISTORICAL_PRESERVE_HOURS = 12
MIN_HISTORICAL_PRESERVE_HOURS = 2
ENV__MAX_DOCUMENT_SIZE_MB = 'NJ_DSS3_MAX_DOCUMENT_SIZE_MB'
DEFAULT_MAX_DOCUMENT_SIZE_MB = 4
MIN_DOCUMENT_SIZE_MB = 2

_HOURS_TO_SECONDS = 60.0 * 60.0
_MB_TO_BYTES = 1024 * 1024


class Config:
    """Configuration for the S3 backend"""
    __slots__ = (
        'bucket', 'base_path', 'aws_config',
        'max_document_bytes',
        'historical_preserve_count', 'historical_preserve_seconds',
        'is_test_mode',
    )

    def __init__(self, env: Dict[str, str]) -> None:
        self.bucket = get_s3_bucket(env)
        self.base_path = get_base_path(env)
        self.aws_config = get_aws_config(env)
        self.max_document_bytes = get_max_document_bytes(env)
        self.historical_preserve_count = get_historical_preserve_count(env)
        self.historical_preserve_seconds = get_historical_preserve_seconds(env)
        self.is_test_mode = get_test_mode_enabled(env)

    def is_valid(self) -> bool:
        """Check if this is a valid setup."""
        if not self.bucket:
            print("[nightjar-ds-aws-s3] Bucket env ({0}) not set.  Cannot run.".format(
                ENV__BUCKET,
            ))
            return False
        if '/' in self.bucket:
            # May find out that buckets with '.' in the name is not allowed.  But for now,
            # assume otherwise.
            print("[nightjar-ds-aws-s3] Bucket env ({0}) invalid ({1}).  Cannot run.".format(
                ENV__BUCKET, self.bucket,
            ))
            return False
        return True

    def get_path(self, path_parts: List[str]) -> str:
        """S3 path for the given path parts."""
        # Need to clean everything up.
        parts: List[str] = []
        if self.base_path:
            parts.append(self.base_path)
        parts.extend(path_parts)
        ret_parts: List[str] = []
        for part in parts:
            while part and part[0] == '/':
                part = part[1:]
            while part and part[-1] == '/':
                part = part[:-1]
            if part:
                ret_parts.append(part)
        return '/'.join(ret_parts)


def create_configuration() -> Config:
    """Create and populate the configuration object."""
    ret = Config(dict(os.environ))

    # This avoids a circular import, and note that this should only be called once.
    from .s3 import set_aws_config  # pylint: disable=C0415

    set_aws_config(ret.aws_config)
    return ret


def get_s3_bucket(env: Dict[str, str]) -> str:
    """Get the s3 bucket name from the environment."""
    return env.get(ENV__BUCKET, '')


def get_base_path(env: Dict[str, str]) -> str:
    """Get the base path from the environment."""
    return env.get(ENV__BASE_PATH, DEFAULT_BASE_PATH)


def get_max_document_bytes(env: Dict[str, str]) -> int:
    """Get the maximum number of bytes a document allowed to be stored in S3."""
    try:
        mb_count = int(env.get(
            ENV__MAX_DOCUMENT_SIZE_MB, str(DEFAULT_MAX_DOCUMENT_SIZE_MB),
        ))
    except ValueError:
        mb_count = DEFAULT_MAX_DOCUMENT_SIZE_MB
    return max(mb_count, MIN_DOCUMENT_SIZE_MB) * _MB_TO_BYTES


def get_historical_preserve_count(env: Dict[str, str]) -> int:
    """Get the number of old versions to keep around."""
    try:
        preserve_count = int(env.get(
            ENV__HISTORICAL_PRESERVE_COUNT, str(DEFAULT_HISTORICAL_PRESERVE_COUNT),
        ))
    except ValueError:
        preserve_count = DEFAULT_HISTORICAL_PRESERVE_COUNT
    return max(MIN_HISTORICAL_PRESERVE_COUNT, preserve_count)


def get_historical_preserve_seconds(env: Dict[str, str]) -> float:
    """Get the number of seconds to preserve historical documents.  When this is exceeded,
    then the preserve count takes effect."""
    try:
        preserve_hours = int(env.get(
            ENV__HISTORICAL_PRESERVE_HOURS, str(DEFAULT_HISTORICAL_PRESERVE_HOURS),
        ))
    except ValueError:
        preserve_hours = DEFAULT_HISTORICAL_PRESERVE_HOURS
    return max(MIN_HISTORICAL_PRESERVE_HOURS, preserve_hours) * _HOURS_TO_SECONDS


def get_aws_config(env: Dict[str, str]) -> Dict[str, str]:
    """Create the AWS config."""
    ret: Dict[str, str] = {}
    for key, value in env.items():
        if key.startswith('AWS_'):
            ret[key] = value
    return ret


def get_test_mode_enabled(env: Dict[str, str]) -> bool:
    """Get the test mode, which is used only for unit testing.
    Note that the env value has a '.' in it, which should be only settable through
    explicit os.environ setting."""
    return env.get('TEST.MODE', 'x') == 'unit-test'
