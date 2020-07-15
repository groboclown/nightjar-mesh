
from typing import Sequence, Iterable, Optional
from ..api.deployment_map import AbcDeploymentMap
from ..api.params import ImplementationParameters, ParamValues
from .deployment_map_aws_cloudmap.config import CLOUDMAP_PARAMETERS, AwsCloudmapConfig
from .deployment_map_cluster.config import ECS_CLUSTER_PARAMETERS, AwsEcsClusterConfig


def get_deployment_map_params() -> Sequence[ImplementationParameters]:
    return (
        CLOUDMAP_PARAMETERS,
        ECS_CLUSTER_PARAMETERS,
    )


SUPPORTED_DEPLOYMENT_MAP_NAMES = (
    *CLOUDMAP_PARAMETERS.aliases,
    *ECS_CLUSTER_PARAMETERS.aliases,
)


def get_deployment_map_impl(
        name: str,
        params: ParamValues,
        initial_namespace_list: Optional[Iterable[str]] = None
) -> AbcDeploymentMap:
    if name in CLOUDMAP_PARAMETERS.aliases:
        from .deployment_map_aws_cloudmap.deployment_map import ServiceDiscoveryDeploymentMap
        return ServiceDiscoveryDeploymentMap(AwsCloudmapConfig(params), initial_namespace_list or [])
    if name in ECS_CLUSTER_PARAMETERS.aliases:
        from .deployment_map_cluster.deployment_map import ClusterTaskDeploymentMap
        return ClusterTaskDeploymentMap(AwsEcsClusterConfig(params), initial_namespace_list or [])

    raise ValueError('Unknown deployment map implementation: {0}; supported types are {1}'.format(
        name, repr(SUPPORTED_DEPLOYMENT_MAP_NAMES),
    ))
