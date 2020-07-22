
"""
Test the wide module.
"""

import unittest
from .. import wide
from ....api.data_store import (
    NamespaceTemplateEntity,
    ServiceColorTemplateEntity,
    GatewayConfigEntity,
    ServiceIdConfigEntity,

    ACTIVITY_TEMPLATE_DEFINITION,
    ACTIVITY_PROXY_CONFIGURATION,
)
from .....protect import PROTECTION_PUBLIC, PROTECTION_PRIVATE


class WideTest(unittest.TestCase):
    """Test cases for the wide functions."""

    def test_get_entity_path(self) -> None:
        """test the different entity types.
        Permutations are performed on the per-type."""

        self.assertEqual(
            wide.get_entity_path('a1b', NamespaceTemplateEntity('n1', PROTECTION_PUBLIC, 'p1')),
            ['content', ACTIVITY_TEMPLATE_DEFINITION, 'a1b', 'gateway', 'n1', 'public', 'p1'],
        )
        self.assertEqual(
            wide.get_entity_path('bbb', ServiceColorTemplateEntity('n2', 'sx', 'cx', 'xyz')),
            ['content', ACTIVITY_TEMPLATE_DEFINITION, 'bbb', 'service', 'n2', 'sx', 'cx', 'xyz'],
        )
        self.assertEqual(
            wide.get_entity_path('1234', GatewayConfigEntity('n3', PROTECTION_PRIVATE, 'abc.txt')),
            [
                'content', ACTIVITY_PROXY_CONFIGURATION, '1234',
                'gateway', 'n3', 'private', 'abc.txt',
            ],
        )
        self.assertEqual(
            wide.get_entity_path(
                '1234', ServiceIdConfigEntity('n4', 'svc-1', 's2', 'c3', 'abc.md')
            ),
            [
                'content', ACTIVITY_PROXY_CONFIGURATION, '1234', 'service', 'n4', 'svc-1',
                's2', 'c3', 'abc.md',
            ],
        )

    def test_parse_template_path(self) -> None:
        """Just check the different entity types.
        Permutations on paths is done on the per-type."""

        self.assertEqual(
            wide.parse_template_path('1234', [
                'content', ACTIVITY_TEMPLATE_DEFINITION, '1234', 'gateway', 'n1', 'default', 'p',
            ]),
            NamespaceTemplateEntity('n1', None, 'p')
        )
        self.assertEqual(
            wide.parse_template_path('1234', [
                'content', ACTIVITY_TEMPLATE_DEFINITION, '1234', 'service',
                '__default__', '__default__', '__default__', 'px',
            ]),
            ServiceColorTemplateEntity(None, None, None, 'px')
        )
        self.assertIsNone(wide.parse_template_path('1234', ['x']))

    def test_parse_config_path(self) -> None:
        """Just check the different entity types.
        Permutations on paths is done on the per-type."""

        self.assertEqual(
            wide.parse_config_path('abc', [
                'content', ACTIVITY_PROXY_CONFIGURATION, 'abc', 'gateway', 'n1', 'public', 'x',
            ]),
            GatewayConfigEntity('n1', PROTECTION_PUBLIC, 'x'),
        )
        self.assertEqual(
            wide.parse_config_path('de', [
                'content', ACTIVITY_PROXY_CONFIGURATION, 'de', 'service', 'a', 'b', 'c', 'd', 'xyz',
            ]),
            ServiceIdConfigEntity('a', 'b', 'c', 'd', 'xyz'),
        )
        self.assertIsNone(
            wide.parse_config_path('f', [
                'content', ACTIVITY_TEMPLATE_DEFINITION, 'f', 'service', 'x', 'y', 'z',
            ])
        )

    def test_get_namespace_template_prefix(self) -> None:
        """Simple prefix checks"""

        self.assertEqual(
            ['content', ACTIVITY_TEMPLATE_DEFINITION, '1', 'gateway'],
            wide.get_namespace_template_prefix('1'),
        )
        self.assertEqual(
            ['content', ACTIVITY_TEMPLATE_DEFINITION, 'abcdefghijklmnop.a.2.2/1@#%@', 'gateway'],
            wide.get_namespace_template_prefix('abcdefghijklmnop.a.2.2/1@#%@'),
        )


# Other functions to test...
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
# parse_gateway_config_path(config: S3EnvConfig, version: str, path: str)
# -> Optional[GatewayConfigEntity]:
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
        """version reference path get test."""
        self.assertEqual(
            wide.get_version_reference_path('act1', '123'),
            [
                'versions', 'act1', '123',
            ],
        )
