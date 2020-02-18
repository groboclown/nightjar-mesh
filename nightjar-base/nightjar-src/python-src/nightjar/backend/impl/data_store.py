
from typing import Sequence
from .data_store_s3.config import S3_PARAMETERS, S3EnvConfig
from ..api.data_store import AbcDataStoreBackend
from ..api.params import ImplementationParameters, ParamValues

SUPPORTED_DATA_STORE_IMPLS = (
    *S3_PARAMETERS.aliases,
)


def get_data_store_params() -> Sequence[ImplementationParameters]:
    return (
        S3_PARAMETERS,
    )


def get_data_store_impl(name: str, parameters: ParamValues) -> AbcDataStoreBackend:
    if name in S3_PARAMETERS.aliases:
        from .data_store_s3.backend import S3Backend
        return S3Backend(S3EnvConfig(parameters))
    raise ValueError('Unknown backend data store implementation: {0}; supported types are {1}'.format(
        name, repr(SUPPORTED_DATA_STORE_IMPLS),
    ))
