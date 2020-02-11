
import unittest
from .mock import MockBackend
from .. import collector
from ..abc_backend import (
    ServiceColorEntity,
    ACTIVITY_TEMPLATE_DEFINITION
)


class TestCollectorDataStore(unittest.TestCase):
    def test_init(self) -> None:
        mock = MockBackend()
        collector.CollectorDataStore(mock)
        self.assertEqual(mock.active_version, ACTIVITY_TEMPLATE_DEFINITION)

    def test_get_service_color_templates_with_defaults(self) -> None:
        mock = MockBackend()
        cds = collector.CollectorDataStore(mock)
        mock.service_color_entities[ServiceColorEntity(None, None, 'p', True)] = 'x0'
        mock.service_color_entities[ServiceColorEntity('s1', None, 'p', True)] = 'x1'
        mock.service_color_entities[ServiceColorEntity('s1', 'c1', 'p', True)] = 'x2'
        mock.service_color_entities[ServiceColorEntity('s2', 'c2', 'p', True)] = 'y2'
        mock.service_color_entities[ServiceColorEntity('s2', 'c3', 'p1', True)] = 'y3'
        mock.service_color_entities[ServiceColorEntity('s2', 'c3', 'p2', True)] = 'y4'

        # Exact match
        ret1 = list(cds.get_service_color_templates([('s1', 'c1')]))
        self.assertEqual(
            ret1,
            [
                (('s1', 'c1'), 'p', 'x2'),
            ]
        )

        # Partial match
        ret2 = list(cds.get_service_color_templates([('s1', 'c2')]))
        self.assertEqual(
            ret2,
            [
                (('s1', 'c2'), 'p', 'x1'),
            ]
        )

        # Default/default match
        ret3 = list(cds.get_service_color_templates([('x1', 'c2')]))
        self.assertEqual(
            ret3,
            [
                (('x1', 'c2'), 'p', 'x0'),
            ]
        )

        # Multiple purpose matches
        ret4 = set(cds.get_service_color_templates([('s2', 'c3')]))
        self.assertEqual(
            ret4,
            {
                (('s2', 'c3'), 'p', 'x0'),
                (('s2', 'c3'), 'p1', 'y3'),
                (('s2', 'c3'), 'p2', 'y4'),
            }
        )
