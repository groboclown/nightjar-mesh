
from .backend import S3Backend
from .config import S3EnvConfig


def create_s3_data_store() -> S3Backend:
    return S3Backend(S3EnvConfig())
