
from typing import Optional
from ...api.params import ParamDef, ParamValues, ImplementationParameters

ENV_BASE_PATH = 'LOCAL_FILE_BASE_PATH'
DEFAULT_BASE_PATH = '.'

PARAM__LOCAL_BASE_PATH = ParamDef[str](
    'local_base_path', ENV_BASE_PATH, ('local-base-path',),
    "(local backend only) root directory, under which all the files are stored",
    DEFAULT_BASE_PATH, str,
)

LOCAL_PARAMETERS = ImplementationParameters(
    'local', ('local-wide',), 'data store which saves each purpose into its own file',
    (
        PARAM__LOCAL_BASE_PATH,
    )
)


class LocalEnvConfig:
    __base_path: str = DEFAULT_BASE_PATH
    __loaded = False

    def __init__(self, values: Optional[ParamValues] = None) -> None:
        if values:
            self.load(values)

    def load(self, values: ParamValues) -> 'LocalEnvConfig':
        self.__base_path = PARAM__LOCAL_BASE_PATH.get_value(values) or DEFAULT_BASE_PATH
        self.__loaded = True
        return self

    @property
    def base_path(self) -> str:
        assert self.__loaded
        return self.__base_path
