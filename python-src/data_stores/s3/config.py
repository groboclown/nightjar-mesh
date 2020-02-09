
from typing import Optional
import os

ENV_BUCKET = 'S3_BUCKET'
ENV_BASE_PATH = 'S3_BASE_PATH'
AWS_REGION = 'AWS_REGION'
AWS_PROFILE = 'AWS_PROFILE'
DEFAULT_BASE_PATH = '/'


class S3EnvConfig:
    __bucket: Optional[str] = None
    __base_path: str = DEFAULT_BASE_PATH
    __region: Optional[str] = None
    __profile: Optional[str] = None
    __loaded = False

    def load(self) -> None:
        if self.__loaded:
            return
        self.__bucket = os.environ.get(ENV_BUCKET, None)
        self.__base_path = os.environ.get(ENV_BASE_PATH, DEFAULT_BASE_PATH)
        self.__region = os.environ.get(AWS_REGION, None)
        self.__profile = os.environ.get(AWS_PROFILE, None)
        self.__loaded = True

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
    def aws_region(self) -> str:
        self.load()
        assert self.__region is not None
        return self.__region

    @property
    def aws_profile(self) -> Optional[str]:
        self.load()
        return self.__profile
