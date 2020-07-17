
"""
S3 Configuration Parameters
"""

# This file must be clean of any boto3 or boto imports.  Likewise, it
# can't import anything that in turn imports those.

from typing import Optional, List
from ..shared_aws import PARAM__AWS_REGION, PARAM__AWS_PROFILE
from ...api.params import ParamDef, ParamValues, ImplementationParameters

ENV_BUCKET = 'S3_BUCKET'
ENV_BASE_PATH = 'S3_BASE_PATH'
ENV_PURGE_BEFORE_DAYS = 'PURGE_BEFORE_DAYS'
DEFAULT_BASE_PATH = '/'

PARAM__S3_BUCKET = ParamDef[str](
    's3_bucket', ENV_BUCKET, ('s3-bucket',),
    "(s3 backend only) s3 bucket to store the files",
    None, str,
)
PARAM__S3_BASE_PATH = ParamDef[str](
    's3_base_path', ENV_BASE_PATH, ('s3-base-path',),
    "(s3 backend only) s3 base path, under which all the files are stored",
    DEFAULT_BASE_PATH, str,
)
PARAM__PURGE_BEFORE_DAYS = ParamDef[int](
    's3_purge_old_versions', ENV_PURGE_BEFORE_DAYS, ('s3-purge-versions-before-days',),
    "Purge expired versions older than this many days.  Set to <= 0 to disable.",
    -1, int, False,
)

S3_PARAMETERS = ImplementationParameters(
    's3', ('s3-wide',), 'data store using each file as its own key in S3',
    (
        PARAM__AWS_REGION, PARAM__AWS_PROFILE,
        PARAM__S3_BUCKET, PARAM__S3_BASE_PATH,
        PARAM__PURGE_BEFORE_DAYS,
    ),
)


class S3EnvConfig:
    """Configuration for the S3 backend"""
    __bucket: Optional[str] = None
    __base_path: str = DEFAULT_BASE_PATH
    __region: Optional[str] = None
    __profile: Optional[str] = None
    __purge_old_versions: bool = False
    __purge_older_than_days: int = 30
    __loaded = False

    def __init__(self, values: Optional[ParamValues] = None) -> None:
        if values:
            self.load(values)

    def load(self, values: ParamValues) -> 'S3EnvConfig':
        """Load the configuration with the values."""
        self.__bucket = PARAM__S3_BUCKET.get_value(values)
        path = PARAM__S3_BASE_PATH.get_value(values) or DEFAULT_BASE_PATH
        while path[0] == '/':
            path = path[1:]
        while path[-1] == '/':
            path = path[:-1]
        self.__base_path = path
        self.__region = PARAM__AWS_REGION.get_value(values)
        self.__profile = PARAM__AWS_PROFILE.get_value(values)
        self.__purge_older_than_days = PARAM__PURGE_BEFORE_DAYS.get_value(values) or -1
        self.__purge_old_versions = self.__purge_older_than_days > 0
        self.__loaded = True
        return self

    @property
    def bucket(self) -> str:
        """The s3 bucket"""
        assert self.__loaded
        assert self.__bucket is not None
        return self.__bucket

    @property
    def base_path(self) -> str:
        """The base path"""
        assert self.__loaded
        return self.__base_path

    @property
    def purge_old_versions(self) -> bool:
        """Should old versions be purged?"""
        assert self.__loaded
        return self.__purge_old_versions

    @property
    def purge_older_than_days(self) -> int:
        """Old versions older than this number of days are purged, if purging is enabled."""
        assert self.__loaded
        return self.__purge_older_than_days

    @property
    def aws_region(self) -> str:
        """AWS region"""
        assert self.__loaded
        assert self.__region is not None
        return self.__region

    @property
    def aws_profile(self) -> Optional[str]:
        """AWS profile"""
        assert self.__loaded
        return self.__profile

    def get_path(self, path_parts: List[str]) -> str:
        """S3 path for the given path parts."""
        if self.base_path:
            return self.base_path + '/' + ('/'.join(path_parts))
        return '/'.join(path_parts)

    def split_key_to_path(self, path: str) -> List[str]:
        """Split this S3 key into path parts."""
        ret: List[str] = []
        if not path.startswith(self.base_path):
            return ret
        for part in path[len(self.base_path):].split('/'):
            if part:
                ret.append(part)
        return ret
