
from typing import Dict, Optional
import os

ENV_BUCKET = 'S3_BUCKET'
ENV_BASE_PATH = 'S3_BASE_PATH'
AWS_REGION = 'AWS_REGION'
AWS_PROFILE = 'AWS_PROFILE'
PURGE_OLD_VERSIONS = 'PURGE_OLD_VERSIONS'
TRUE_VALUES = ('active', 'true', 'yes', 'enabled', '1')
PURGE_BEFORE_DAYS = 'PURGE_BEFORE_DAYS'
DEFAULT_BASE_PATH = '/'


class S3EnvConfig:
    __bucket: Optional[str] = None
    __base_path: str = DEFAULT_BASE_PATH
    __region: Optional[str] = None
    __profile: Optional[str] = None
    __purge_old_versions: bool = False
    __purge_older_than_days: int = 30
    __loaded = False

    def load(self, environ: Optional[Dict[str, str]] = None) -> 'S3EnvConfig':
        if self.__loaded:
            return self
        if not environ:
            environ = dict(os.environ)
        self.__bucket = environ.get(ENV_BUCKET, None)
        self.__base_path = environ.get(ENV_BASE_PATH, DEFAULT_BASE_PATH)
        while self.__base_path[-1] == '/':
            self.__base_path = self.__base_path[:-1]
        # S3 indicates that the base path must not start with a '/'
        while self.__base_path[0] == '/':
            self.__base_path = self.__base_path[1:]
        self.__region = environ.get(AWS_REGION, None)
        self.__profile = environ.get(AWS_PROFILE, None)
        self.__purge_old_versions = environ.get(PURGE_OLD_VERSIONS, 'true').strip().lower() in TRUE_VALUES
        self.__purge_older_than_days = int(environ.get(PURGE_BEFORE_DAYS, '30'))
        self.__loaded = True
        return self

    @property
    def bucket(self) -> str:
        self.load()
        assert self.__bucket is not None
        return self.__bucket

    @property
    def base_path(self) -> str:
        self.load()
        return self.__base_path

    @property
    def purge_old_versions(self) -> bool:
        return self.__purge_old_versions

    @property
    def purge_older_than_days(self) -> int:
        return self.__purge_older_than_days

    @property
    def aws_region(self) -> str:
        self.load()
        assert self.__region is not None
        return self.__region

    @property
    def aws_profile(self) -> Optional[str]:
        self.load()
        return self.__profile
