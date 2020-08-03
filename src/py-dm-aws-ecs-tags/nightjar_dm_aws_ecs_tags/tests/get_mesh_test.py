
"""Test the get_mesh module"""

import unittest
from .. import get_mesh
# from ..config import Config
from ..ecs import (
    EcsTask, RouteInfo,
    TAG__NAMESPACE,
    TAG__MODE,
    TAG__SERVICE,
    TAG__COLOR,
    TAG__ROUTE_PORT_INDEX_PREFIX, TAG__ROUTE_PORT,
    TAG__PROTOCOL, TAG__PREFER_GATEWAY,
)


class GetMeshTest(unittest.TestCase):  # pylint: disable=R0904
    """Test functions in get_mesh."""

    def test_create_namespace_config__none(self) -> None:
        """Test create_namespace_config with no values"""
        res = get_mesh.create_namespace_config('n1', [], [])
        self.assertEqual({
            'namespace': 'n1',
            'network-id': 'n1',
            'gateways': {'protocol': 'HTTP1.1', 'prefer-gateway': False, 'instances': []},
            'service-colors': [],
        }, res)

    def test_create_gateway_config__none(self) -> None:
        """Test create_gateway_config with no values"""
        res = get_mesh.create_gateway_config([])
        self.assertEqual({
            'protocol': 'HTTP1.1',
            'prefer-gateway': False,
            'instances': [],
        }, res)

    def test_create_gateway_config__one(self) -> None:
        """Test create_gateway_config with no values"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {'20': 21}, {}, {},
            {TAG__PROTOCOL: 'xyz', TAG__PREFER_GATEWAY: 'yes'},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'GATEWAY'},
        )
        res = get_mesh.create_gateway_config([task_1])
        self.assertEqual({
            'protocol': 'xyz',
            'prefer-gateway': True,
            'instances': [{
                'ipv4': '1.2.3.4',
                'port': 21,
            }],
        }, res)

    def test_create_service_color_configs__none(self) -> None:
        """Test create_service_color_configs with no values"""
        res = get_mesh.create_service_color_configs([])
        self.assertEqual([], res)

    def test_create_service_color_configs__one(self) -> None:
        """Test create_service_color_configs with no values"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {'20': 21}, {}, {},
            {
                'NJ_ROUTE_1': '/p1/', TAG__ROUTE_PORT_INDEX_PREFIX + '1': '20',
                'NJ_NAMESPACE_PORT_12': 'n2:90',
            },
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's', TAG__COLOR: 'c'},
        )
        res = get_mesh.create_service_color_configs([task_1])
        self.assertEqual([{
            'service': 's',
            'color': 'c_21',
            'routes': [{
                'default-access': True,
                'namespace-access': [],
                'path-match': {'match-type': 'prefix', 'value': '/p1/'},
                'weight': 1,
            }],
            'instances': [{'ipv4': '1.2.3.4', 'port': 21}],
            'namespace-egress': [{
                'namespace': 'n2',
                'interfaces': [{'ipv4': '127.0.0.1', 'port': 90}],
            }],
        }], res)

    def test_create_service_color_routes__none(self) -> None:
        """Test create_service_color_routes with no values"""
        res = get_mesh.create_service_color_routes([])
        self.assertEqual([], res)

    def test_create_service_color_routes__all_types(self) -> None:
        """Test create_service_color_routes with no values"""
        route_1 = RouteInfo(1, '/v1', '12', 12, 11)
        route_2 = RouteInfo(2, '/v2/', '12', 12, 12)
        route_3 = RouteInfo(3, '!/v3', '12', 12, 13)
        route_4 = RouteInfo(4, '!/v4/', '12', 12, 14)
        route_5 = RouteInfo(5, '+/v5', '12', 12, 15)
        route_6 = RouteInfo(6, '+/v6/', '12', 12, 16)
        route_7 = RouteInfo(7, '{"t":16}', '12', 12, 17)
        res = get_mesh.create_service_color_routes([
            route_1, route_2, route_3, route_4, route_5, route_6, route_7,
        ])
        self.assertEqual([
            {
                'default-access': True,
                'namespace-access': [],
                'path-match': {'match-type': 'exact', 'value': '/v1'},
                'weight': 11,
            },
            {
                'default-access': True,
                'namespace-access': [],
                'path-match': {'match-type': 'prefix', 'value': '/v1/'},
                'weight': 11,
            },
            {
                'default-access': True,
                'namespace-access': [],
                'path-match': {'match-type': 'prefix', 'value': '/v2/'},
                'weight': 12,
            },
            {
                'default-access': False,
                'namespace-access': [],
                'path-match': {'match-type': 'exact', 'value': '/v3'},
                'weight': 13,
            },
            {
                'default-access': False,
                'namespace-access': [],
                'path-match': {'match-type': 'prefix', 'value': '/v3/'},
                'weight': 13,
            },
            {
                'default-access': False,
                'namespace-access': [],
                'path-match': {'match-type': 'prefix', 'value': '/v4/'},
                'weight': 14,
            },
            {
                'default-access': True,
                'namespace-access': [],
                'path-match': {'match-type': 'exact', 'value': '/v5'},
                'weight': 15,
            },
            {
                'default-access': True,
                'namespace-access': [],
                'path-match': {'match-type': 'prefix', 'value': '/v5/'},
                'weight': 15,
            },
            {
                'default-access': True,
                'namespace-access': [],
                'path-match': {'match-type': 'prefix', 'value': '/v6/'},
                'weight': 16,
            },
            {'t': 16},
        ], res)

    def test_create_service_color_instances__none(self) -> None:
        """Test create_service_color_instances with no values"""
        res = get_mesh.create_service_color_instances([], 12)
        self.assertEqual([], res)

    def test_create_service_color_instances__one(self) -> None:
        """Test create_service_color_instances with no values"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        res = get_mesh.create_service_color_instances([task_1], 12)
        self.assertEqual([{
            'ipv4': '1.2.3.4',
            'port': 12,
        }], res)

    def test_create_service_color_instances__two(self) -> None:
        """Test create_service_color_instances with no values"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        task_2 = EcsTask(
            't2', 'ta1', 'td1', 'cia1', '1.2.3.5',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        res = get_mesh.create_service_color_instances([task_1, task_2], 12)
        self.assertEqual([
            {
                'ipv4': '1.2.3.4',
                'port': 12,
            },
            {
                'ipv4': '1.2.3.5',
                'port': 12,
            },
        ], res)

    def test_create_service_color_namespace_egress__none(self) -> None:
        """Test create_service_color_namespace_egress with no values"""
        res = get_mesh.create_service_color_namespace_egress([])
        self.assertEqual([], res)

    def test_create_service_color_namespace_egress__one_no_egress(self) -> None:
        """Test create_service_color_namespace_egress with no values"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        res = get_mesh.create_service_color_namespace_egress([task_1])
        self.assertEqual([], res)

    def test_create_service_color_namespace_egress__one_egress(self) -> None:
        """Test create_service_color_namespace_egress with no values"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {},
            {'NJ_NAMESPACE_PORT_12': 'n2:90'},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        res = get_mesh.create_service_color_namespace_egress([task_1])
        self.assertEqual([{
            'namespace': 'n2',
            'interfaces': [{'ipv4': '127.0.0.1', 'port': 90}],
        }], res)

    def test_create_service_color_namespace_egress__two_tasks_one_egress(self) -> None:
        """Test create_service_color_namespace_egress with no values"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {},
            {'NJ_NAMESPACE_PORT_12': 'n2:90'},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        task_2 = EcsTask(
            't2', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {},
            {'NJ_NAMESPACE_PORT_12': 'n2:90'},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        res = get_mesh.create_service_color_namespace_egress([task_1, task_2])
        self.assertEqual([{
            'namespace': 'n2',
            'interfaces': [{'ipv4': '127.0.0.1', 'port': 90}],
        }], res)

    def test_create_service_color_namespace_egress__one_tasks_two_egress(self) -> None:
        """Test create_service_color_namespace_egress with no values"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {},
            {'NJ_NAMESPACE_PORT_12': 'n2:90', 'NJ_NAMESPACE_PORT_999': 'nn33:12'},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        res = get_mesh.create_service_color_namespace_egress([task_1])
        self.assertEqual(sorted([
            {
                'namespace': 'n2',
                'interfaces': [{'ipv4': '127.0.0.1', 'port': 90}],
            },
            {
                'namespace': 'nn33',
                'interfaces': [{'ipv4': '127.0.0.1', 'port': 12}],
            },
        ], key=lambda x: x['namespace']), sorted(res, key=lambda x: x['namespace']))

    def test_get_routes_by_port__one_route(self) -> None:
        """Test get_routes_by_port with one task/route"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {'20': 21}, {}, {},
            {'NJ_ROUTE_1': '/p1', TAG__ROUTE_PORT_INDEX_PREFIX + '1': '20'},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's', TAG__COLOR: 'c'},
        )
        res = get_mesh.get_routes_by_port([task_1])
        self.assertEqual(repr({
            21: [RouteInfo(1, '/p1', '20', 21, 1)],
        }), repr(res))

    def test_get_routes_by_port__two_routes_one_port(self) -> None:
        """Test get_routes_by_port with one task/route"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {'20': 21}, {}, {},
            {'NJ_ROUTE_1': '/p1', 'NJ_ROUTE_2': '/p2', TAG__ROUTE_PORT: '20'},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's', TAG__COLOR: 'c'},
        )
        res = get_mesh.get_routes_by_port([task_1])
        self.assertEqual(repr({
            21: [RouteInfo(1, '/p1', '20', 21, 1), RouteInfo(2, '/p2', '20', 21, 1)],
        }), repr(res))

    def test_get_routes_by_port__two_routes_two_ports(self) -> None:
        """Test get_routes_by_port with one task/route"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {'20': 21, '22': 22}, {}, {},
            {
                'NJ_ROUTE_1': '/p1', TAG__ROUTE_PORT_INDEX_PREFIX + '1': '20',
                'NJ_ROUTE_2': '/p2', TAG__ROUTE_PORT_INDEX_PREFIX + '2': '22',
            },
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's', TAG__COLOR: 'c'},
        )
        res = get_mesh.get_routes_by_port([task_1])
        self.assertEqual(repr({
            21: [RouteInfo(1, '/p1', '20', 21, 1)],
            22: [RouteInfo(2, '/p2', '22', 22, 1)],
        }), repr(res))

    def test_sort_tasks_by_service_color__empty(self) -> None:
        """Test sort_tasks_by_service_color with no values"""
        res = get_mesh.sort_tasks_by_service_color([])
        self.assertEqual({}, res)

    def test_sort_tasks_by_service_color__one(self) -> None:
        """Test sort_tasks_by_service_color with one service"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's', TAG__COLOR: 'c'},
        )
        res = get_mesh.sort_tasks_by_service_color([task_1])
        self.assertEqual({('s', 'c'): [task_1]}, res)

    def test_sort_tasks_by_service_color__many(self) -> None:
        """Test sort_tasks_by_service_color with many services"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        task_2 = EcsTask(
            't2', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c1'},
        )
        task_3 = EcsTask(
            't3', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's1', TAG__COLOR: 'c2'},
        )
        task_4 = EcsTask(
            't4', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's2', TAG__COLOR: 'c2'},
        )
        res = get_mesh.sort_tasks_by_service_color([task_1, task_2, task_3, task_4])
        self.assertEqual({
            ('s1', 'c1'): [task_1, task_2],
            ('s1', 'c2'): [task_3],
            ('s2', 'c2'): [task_4],
        }, res)

    def test_sort_tasks_by_namespace__empty(self) -> None:
        """Test sort_tasks_by_namespace with no values"""
        res = get_mesh.sort_tasks_by_namespace([])
        self.assertEqual({}, res)

    def test_sort_tasks_by_namespace__one_namespace__no_gateway_service(self) -> None:
        """Test sort_tasks_by_namespace with no value"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {}, {TAG__NAMESPACE: 'n1'},
        )

        res = get_mesh.sort_tasks_by_namespace([task_1])
        self.assertEqual({'n1': ([], [])}, res)

    def test_sort_tasks_by_namespace__one_service(self) -> None:
        """Test sort_tasks_by_namespace with no value"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's', TAG__COLOR: 'c'},
        )

        res = get_mesh.sort_tasks_by_namespace([task_1])
        self.assertEqual({'n1': ([], [task_1])}, res)

    def test_sort_tasks_by_namespace__one_gateway(self) -> None:
        """Test sort_tasks_by_namespace with no value"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'GATEWAY'},
        )

        res = get_mesh.sort_tasks_by_namespace([task_1])
        self.assertEqual({'n1': ([task_1], [])}, res)

    def test_sort_tasks_by_namespace__multiple(self) -> None:
        """Test sort_tasks_by_namespace with no value"""
        task_1 = EcsTask(
            't1', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'GATEWAY'},
        )
        task_2 = EcsTask(
            't2', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's2', TAG__COLOR: 'c'},
        )
        task_3 = EcsTask(
            't3', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'GATEWAY'},
        )
        task_4 = EcsTask(
            't4', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n1', TAG__MODE: 'SERVICE', TAG__SERVICE: 's4', TAG__COLOR: 'c'},
        )
        task_5 = EcsTask(
            't5', 'ta1', 'td1', 'cia1', '1.2.3.4',
            {}, {}, {}, {},
            {TAG__NAMESPACE: 'n2', TAG__MODE: 'GATEWAY'},
        )

        res = get_mesh.sort_tasks_by_namespace([task_1, task_2, task_3, task_4, task_5])
        self.assertEqual({
            'n1': ([task_1, task_3], [task_2, task_4]),
            'n2': ([task_5], []),
        }, res)
