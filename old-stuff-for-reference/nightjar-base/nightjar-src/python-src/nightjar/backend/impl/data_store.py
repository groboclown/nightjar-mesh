
"""Data store implementation loader and configurator."""

from typing import Sequence
from .data_store_s3.config import S3_PARAMETERS, S3EnvConfig
from .data_store_local.config import LOCAL_PARAMETERS, LocalEnvConfig
from ..api.data_store import AbcDataStoreBackend
from ..api.params import ImplementationParameters, ParamValues


SUPPORTED_DATA_STORE_IMPLS = (
    *S3_PARAMETERS.aliases,
    *LOCAL_PARAMETERS.aliases,
)


def get_data_store_params() -> Sequence[ImplementationParameters]:
    """All the implementation parameters."""
    return (
        S3_PARAMETERS,
        LOCAL_PARAMETERS,
    )


def get_data_store_impl(name: str, parameters: ParamValues) -> AbcDataStoreBackend:
    """Find the implementation of the data store and configure it."""
    if name in S3_PARAMETERS.aliases:
        from .data_store_s3.backend import S3Backend  # pylint: disable=C0415
        return S3Backend(S3EnvConfig(parameters))
    if name in LOCAL_PARAMETERS.aliases:
        from .data_store_local.backend import LocalFileBackend  # pylint: disable=C0415
        return LocalFileBackend(LocalEnvConfig(parameters))
    raise ValueError(
        'Unknown backend data store implementation: {0}; supported types are {1}'.format(
            name, repr(SUPPORTED_DATA_STORE_IMPLS),
        ),
    )
