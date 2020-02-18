
from ..api.params import ParamDef

ENV_AWS_REGION = 'AWS_REGION'
AWS_PROFILE_ENV = 'AWS_PROFILE'

PARAM__AWS_REGION = ParamDef[str](
    'aws_region', ENV_AWS_REGION, ('aws-region', 'region'),
    "AWS region to connect to", None, str
)

PARAM__AWS_PROFILE = ParamDef[str](
    name='aws_profile',
    env_name=AWS_PROFILE_ENV,
    arg_names=('aws-profile', 'profile',),
    help_text="AWS Profile to use as credentials",
    default_value=None,
    var_type=str,
    required=False
)
