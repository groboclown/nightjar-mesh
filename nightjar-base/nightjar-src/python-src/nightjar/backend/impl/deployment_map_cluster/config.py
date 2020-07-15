
from typing import List, Optional
from ...api import ParamDef, ParamValues, ImplementationParameters
from ..shared_aws import PARAM__AWS_REGION, PARAM__AWS_PROFILE


ENV_ECS_CLUSTER = 'ECS_CLUSTER'
ENV_REQUIRED_TAG_NAME_VALUE = 'ECS_CLUSTER_REQUIRED_TAG_NAME_VALUE'


PARAM__ECS_CLUSTERS = ParamDef[str](
    name='ecs_cluster',
    env_name=ENV_ECS_CLUSTER,
    arg_names=('ecs-cluster', 'cluster',),
    help_text="Comma-separated list of cluster names to scan for tasks",
    default_value="default",
    var_type=str,
    required=True,
)


PARAM__REQUIRED_TAG_NAME_VALUE = ParamDef[str](
    name='ecs_cluster_required_tag_name_value',
    env_name=ENV_REQUIRED_TAG_NAME_VALUE,
    arg_names=('expected-tag-name-value',),
    help_text="If given, this tag name and value, in the form `name:value`, must be on a task to be included in routing",
    default_value=None,
    var_type=str,
    required=False,
)


ECS_CLUSTER_PARAMETERS = ImplementationParameters(
    name='ecs-cluster', aliases=('cluster', 'ecs-tasks',),
    description="Reads the tags of tasks running in a cluster",
    params=(
        PARAM__AWS_PROFILE, PARAM__AWS_REGION,
        PARAM__ECS_CLUSTERS, PARAM__REQUIRED_TAG_NAME_VALUE,
    )
)


class AwsEcsClusterConfig:
    def __init__(self, params: Optional[ParamValues] = None) -> None:
        self.aws_region: Optional[str] = None
        self.aws_profile: Optional[str] = None
        self.cluster_names: List[str] = []
        self.required_tag_name: Optional[str] = None
        self.required_tag_value: Optional[str] = None
        if params:
            self.load(params)

    def load(self, params: ParamValues) -> 'AwsEcsClusterConfig':
        self.aws_region = PARAM__AWS_REGION.get_value(params)
        self.aws_profile = PARAM__AWS_PROFILE.get_value(params)
        cluster_names = PARAM__ECS_CLUSTERS.get_value(params)
        if cluster_names:
            self.cluster_names = [
                name.strip()
                for name in cluster_names.split(',')
            ]
        tag_value = PARAM__REQUIRED_TAG_NAME_VALUE.get_value(params)
        if tag_value:
            index = tag_value.find('.')
            if index > 0:
                self.required_tag_name = tag_value[:index].strip()
                self.required_tag_value = tag_value[index+1:].strip()
            else:
                self.required_tag_name = tag_value.strip()
                self.required_tag_value = None
        return self
