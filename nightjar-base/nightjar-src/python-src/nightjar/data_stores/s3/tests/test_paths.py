
from typing import List, Tuple, Optional, Any
import unittest
from .. import paths
from ..config import (
    S3EnvConfig, ENV_BUCKET, ENV_BASE_PATH, AWS_REGION,
)
from ...abc_backend import (
    NamespaceTemplateEntity,
    ServiceColorTemplateEntity,
    GatewayConfigEntity,
    ServiceIdConfigEntity,

    ACTIVITY_TEMPLATE_DEFINITION,
    ACTIVITY_PROXY_CONFIGURATION,
)
from ....protect import as_route_protection

PUBLIC = as_route_protection('public')


class PathsTest(unittest.TestCase):
    config = S3EnvConfig().load({ENV_BUCKET: 's3bucket', ENV_BASE_PATH: '//p1/a1'})

# get_entity_path(config: S3EnvConfig, version: str, entity: Entity) -> str:
    def test_get_entity_path(self) -> None:
        # Just test the different entity types.
        # Permutations are performed on the per-type.
        self.assertEqual(
            paths.get_entity_path(self.config, 'a1b', NamespaceTemplateEntity('n1', PUBLIC, 'p1')),
            'p1/a1/content/template-creation/a1b/gateway/n1/public/p1'
        )

# parse_template_path(config: S3EnvConfig, version: str, path: str) -> Optional[TemplateEntity]:
# get_namespace_template_prefix(config: S3EnvConfig, version: str) -> str:
# get_namespace_template_path(
#             config: S3EnvConfig, version: str,
#             entity: NamespaceTemplateEntity,
#     ) -> str:
# parse_namespace_template_path(config: S3EnvConfig, version: str, path: str) -> Optional[
#         NamespaceTemplateEntity]:
# get_service_color_template_prefix(config: S3EnvConfig, version: str) -> str:
# get_service_color_template_path(
#             config: S3EnvConfig, version: str,
#             entity: ServiceColorTemplateEntity,
#     ) -> str:
# parse_service_color_template_path(
#             config: S3EnvConfig, version: str, path: str
#     ) -> Optional[ServiceColorTemplateEntity]:
# get_gateway_config_prefix(config: S3EnvConfig, version: str) -> str:
# get_gateway_config_path(
#             config: S3EnvConfig, version: str,
#             entity: GatewayConfigEntity,
#     ) -> str:
# parse_gateway_config_path(config: S3EnvConfig, version: str, path: str) -> Optional[GatewayConfigEntity]:
# get_service_id_config_prefix(config: S3EnvConfig, version: str) -> str:
# get_service_id_config_path(
#             config: S3EnvConfig, version: str,
#             entity: ServiceIdConfigEntity,
#     ) -> str:
# parse_service_id_config_path(
#             config: S3EnvConfig, version: str, path: str
#     ) -> Optional[ServiceIdConfigEntity]:
# get_protection_path_name(is_public: Optional[bool]) -> str:
# parse_protection(part: str) -> Union[str, Optional[bool]]:
# parse_namespace(part: str) -> Optional[str]:
# parse_service(part: str) -> Optional[str]:
# parse_color(part: str) -> Optional[str]:
# get_activity_prefix(config: S3EnvConfig, version: str, activity: str) -> str:
# parse_activity(config: S3EnvConfig, version: str, path: str) -> Optional[str]:
# get_version_reference_prefix(config: S3EnvConfig, activity: str) -> str:
# parse_version_reference_path(config: S3EnvConfig, activity: str, path: str) -> Optional[str]:

    def test_get_version_reference_path(self) -> None:
        self.assertEqual(
            paths.get_version_reference_path(self.config, 'act1', '123'),
            'p1/a1/versions/act1/123'
        )
