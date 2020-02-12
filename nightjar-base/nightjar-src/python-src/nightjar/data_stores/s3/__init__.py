
from .backend import S3Backend
from .config import (
    S3EnvConfig,
    ENV_BASE_PATH,
    ENV_BUCKET,
    AWS_REGION,
    AWS_PROFILE,
    PURGE_BEFORE_DAYS,
    PURGE_OLD_VERSIONS,
)


def create_s3_data_store() -> S3Backend:
    return S3Backend(S3EnvConfig())
