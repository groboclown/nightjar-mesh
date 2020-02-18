
from typing import Optional
from ...api import ParamValues, ImplementationParameters
from ..shared_aws import PARAM__AWS_REGION, PARAM__AWS_PROFILE


CLOUDMAP_PARAMETERS = ImplementationParameters(
    name='cloud-map', aliases=('service-discovery', 'servicediscovery', 'cloudmap',),
    description="Reads service registration from the AWS Cloud Map API.  Requires additional service instance; see the documentation for details",
    params=(
        PARAM__AWS_PROFILE, PARAM__AWS_REGION,
    )
)


class AwsCloudmapConfig:
    aws_region: Optional[str]
    aws_profile: Optional[str]

    def __init__(self, params: Optional[ParamValues] = None) -> None:
        self.aws_region = None
        self.aws_profile = None
        if params:
            self.load(params)

    def load(self, params: ParamValues) -> 'AwsCloudmapConfig':
        self.aws_region = PARAM__AWS_REGION.get_value(params)
        self.aws_profile = PARAM__AWS_PROFILE.get_value(params)
        return self
