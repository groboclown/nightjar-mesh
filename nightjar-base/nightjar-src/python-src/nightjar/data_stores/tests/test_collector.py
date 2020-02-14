
import unittest
from .mock import MockBackend
from .. import collector
from ..abc_backend import (
    ACTIVITY_TEMPLATE_DEFINITION,
    ServiceColorTemplateEntity,
)


class TestCollectorDataStore(unittest.TestCase):
    def test_init(self) -> None:
        mock = MockBackend()
        collector.CollectorDataStore(mock)
        self.assertEqual(mock.active_versions, set(ACTIVITY_TEMPLATE_DEFINITION))

    def test_get_service_color_templates_with_defaults(self) -> None:
        mock = MockBackend()
        cds = collector.CollectorDataStore(mock)
        x0 = ServiceColorTemplateEntity(None, None, None, 'p')
        mock.service_color_entities[x0] = 'x0'
        x1 = ServiceColorTemplateEntity('n', 's1', None, 'p')
        mock.service_color_entities[x1] = 'x1'
        x2 = ServiceColorTemplateEntity('n', 's1', 'c1', 'p')
        mock.service_color_entities[x2] = 'x2'
        y2 = ServiceColorTemplateEntity('n', 's2', 'c2', 'p')
        mock.service_color_entities[y2] = 'y2'
        y3 = ServiceColorTemplateEntity('n', 's2', 'c3', 'p1')
        mock.service_color_entities[y3] = 'y3'
        y4 = ServiceColorTemplateEntity('n', 's2', 'c3', 'p2')
        mock.service_color_entities[y4] = 'y4'

        # Exact match
        ret1 = list(cds.get_service_color_templates([('n', 'si1', 's1', 'c1')]))
        self.assertEqual(
            ret1,
            [
                collector.MatchedServiceColorTemplate('n', 'si1', 's1', 'c1', x2),
            ]
        )

        # Partial match
        ret2 = list(cds.get_service_color_templates([('n', 'si2', 's1', 'c2')]))
        self.assertEqual(
            ret2,
            [
                collector.MatchedServiceColorTemplate('n', 'si2', 's1', 'c2', x1),
            ]
        )

        # Default/default match
        ret3 = list(cds.get_service_color_templates([('n', 'si3', 'x1', 'c2')]))
        self.assertEqual(
            ret3,
            [
                collector.MatchedServiceColorTemplate('n', 'si3', 'x1', 'c2', x0),
            ]
        )

        # Multiple purpose matches
        ret4 = set(cds.get_service_color_templates([('n', 'si4', 's2', 'c3')]))
        self.assertEqual(
            ret4,
            {
                collector.MatchedServiceColorTemplate('n', 'si4', 's2', 'c3', x0),
                collector.MatchedServiceColorTemplate('n', 'si4', 's2', 'c3', y3),
                collector.MatchedServiceColorTemplate('n', 'si4', 's2', 'c3', y4),
            }
        )
