
from typing import Optional
from ...api import ParamValues, ImplementationParameters, ParamDef


DOCKER_HOST = 'DOCKER_HOST'
DOCKER_TLS_CERT = 'DOCKER_TLS_CERT'
DOCKER_TLS_KEY = 'DOCKER_TLS_KEY'


PARAM__DOCKER_HOST = ParamDef[str](
    name='docker_host',
    env_name=DOCKER_HOST,
    arg_names=('docker-host',),
    help_text="The connection to the docker daemon.",
    default_value='unix:///var/run/docker.sock',
    var_type=str,
    required=False
)

PARAM__DOCKER_TLS_CERT = ParamDef[str](
    name='docker_tls_cert',
    env_name=DOCKER_TLS_CERT,
    arg_names=('docker-tls-cert',),
    help_text="Use TLS, and trust certs signed only by this CA.",
    default_value=None,
    var_type=str,
    required=False
)

PARAM__DOCKER_TLS_KEY = ParamDef[str](
    name='docker_tls_key',
    env_name=DOCKER_TLS_KEY,
    arg_names=('docker-tls-key',),
    help_text="Path to the TLS key.",
    default_value=None,
    var_type=str,
    required=False
)


DOCKER_PARAMETERS = ImplementationParameters(
    name='docker-map', aliases=('docker',),
    description="Reads the service ports from the running docker instances",
    params=(
        PARAM__DOCKER_HOST, PARAM__DOCKER_TLS_CERT, PARAM__DOCKER_TLS_KEY,
    )
)


class DockerConfig:
    __slots__ = ('host', 'tls_cert', 'tls_key', 'use_tls', 'tls_verify')

    def __init__(self) -> None:
        self.host = PARAM__DOCKER_HOST.default_value
        self.tls_cert = PARAM__DOCKER_TLS_CERT.default_value
        self.tls_key = PARAM__DOCKER_TLS_KEY.default_value
        self.use_tls = False
        self.tls_verify = False

    def load(self, params: ParamValues) -> 'DockerConfig':
        self.host = PARAM__DOCKER_HOST.get_value(params)
        self.tls_cert = PARAM__DOCKER_TLS_CERT.get_value(params)
        self.tls_key = PARAM__DOCKER_TLS_KEY.get_value(params)
        # use_tls
        # tls_verify
        return self
