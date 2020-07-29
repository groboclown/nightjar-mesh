
"""
Test the gateway module.
"""

from typing import Dict, Any
import unittest
from .. import gateway, common
from ...validation import validate_discovery_map


class GatewayTest(unittest.TestCase):
    """
    Test the functions in the gateway module.
    Because the module is based around parsing a valid discovery-map output
    data structure, all the tests first construct a well defined discovery
    map data structure, then pass in the required parts to the gateway function
    under test.  This ensures that the tests are using well-defined data,
    which is especially true when the discovery map data format is in flux.
    """

    def test_group_service_colors_by_route(self) -> None:
        """Test group_service_colors_by_route"""

        self.maxDiff = None  # pylint: disable=C0103

        # For this test, have two service colors with a shared route, and a third one
        # that's independent.
        route_1 = _mk_route({'path-match': {'match-type': 'prefix', 'value': '/a'}})
        route_2 = _mk_route({'path-match': {'match-type': 'exact', 'value': '/a'}})
        route_3 = _mk_route({
            'path-match': {'match-type': 'prefix', 'value': '/a'},
            'headers': [
                {'header-name': 'n', 'match-type': 'present', 'value': ''},
            ],
        })
        route_matcher_1 = gateway.get_route_matcher_key(route_1)
        route_matcher_2 = gateway.get_route_matcher_key(route_2)
        route_matcher_3 = gateway.get_route_matcher_key(route_3)
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [
                    _mk_service_color({
                        'service': 's1', 'color': 'c1',
                        'routes': [route_1],
                    }),
                    _mk_service_color({
                        'service': 's1', 'color': 'c2',
                        'routes': [route_1, route_2],
                    }),
                    _mk_service_color({
                        'service': 's2', 'color': 'c1',
                        'routes': [
                            route_2, route_3,
                            _mk_route({'default-protection': 'private'}),
                        ],
                    }),
                ],
            })],
        })
        res = gateway.group_service_colors_by_route(
            discovery_map['namespaces'][0]['service-colors']
        )
        self.assertEqual(
            {
                route_matcher_1: [('c-s1-c1', route_1), ('c-s1-c2', route_1)],
                route_matcher_2: [('c-s1-c2', route_2), ('c-s2-c1', route_2)],
                route_matcher_3: [('c-s2-c1', route_3)],
            },
            res,
        )

    def test_get_route_matcher_key__full(self) -> None:
        """Test get_route_matcher_key with a fully defined structure."""
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'path-match': {
                            'match-type': 'exact', 'value': '/x/y',
                            'case-sensitive': False,
                        },
                        'headers': [
                            {
                                'header-name': 'ab', 'match-type': 'exact', 'value': 'cd',
                                'invert': True, 'case-sensitive': False,
                            },
                            {
                                'header-name': 'ef', 'match-type': 'regex', 'value': '^gh$',
                                'invert': False, 'case-sensitive': True,
                            },
                        ],
                        'query-parameters': [
                            {
                                'parameter-name': 'ij', 'match-type': 'prefix', 'value': 'kl',
                                'case-sensitive': False,
                            },
                            {
                                'parameter-name': 'mn', 'match-type': 'suffix', 'value': 'opq',
                                'case-sensitive': True,
                            },
                        ],
                    })],
                })],
            })],
        })
        res = gateway.get_route_matcher_key(
            discovery_map['namespaces'][0]['service-colors'][0]['routes'][0]
        )
        self.assertEqual(
            common.RouteMatcher(
                common.RoutePathMatcher('/x/y', 'exact', False),
                [
                    common.HeaderQueryMatcher('ab', 'exact', False, 'cd', True),
                    common.HeaderQueryMatcher('ef', 'regex', True, '^gh$', False),
                ], [
                    common.HeaderQueryMatcher('ij', 'prefix', False, 'kl', False),
                    common.HeaderQueryMatcher('mn', 'suffix', True, 'opq', False),
                ],
            ),
            res,
        )

    def test_get_route_matcher_key__bare(self) -> None:
        """Test get_route_matcher_key with the barest possible arguments."""
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/'},
                    })],
                })],
            })],
        })
        res = gateway.get_route_matcher_key(
            discovery_map['namespaces'][0]['service-colors'][0]['routes'][0]
        )
        self.assertEqual(
            common.RouteMatcher(
                common.RoutePathMatcher('/', 'exact', True),
                [], [],
            ),
            res,
        )

    def test_parse_header_query_matcher__defaults__allow_ignore(self) -> None:
        """Test parse_header_query_matcher with default values."""
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'headers': [{
                            'header-name': 'hd2',
                            'match-type': 'present',
                            'value': '',
                        }],
                    })],
                })],
            })],
        })
        res = gateway.parse_header_query_matcher(
            discovery_map['namespaces'][0]['service-colors'][0]['routes'][0]['headers'][0],
            'header-name',
            True,
        )
        self.assertEqual(
            common.HeaderQueryMatcher(
                name='hd2', match_type='present', case_sensitive=True,
                match_value='', invert=False,
            ),
            res,
        )

    def test_parse_header_query_matcher__full__allow_ignore(self) -> None:
        """Test parse_header_query_matcher with default values."""
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'headers': [{
                            'header-name': 'hd1',
                            'match-type': 'regex',
                            'value': 'dec',
                            'case-sensitive': False,
                            'invert': True,
                        }],
                    })],
                })],
            })],
        })
        res = gateway.parse_header_query_matcher(
            discovery_map['namespaces'][0]['service-colors'][0]['routes'][0]['headers'][0],
            'header-name',
            True,
        )
        self.assertEqual(
            common.HeaderQueryMatcher(
                name='hd1', match_type='regex', case_sensitive=False,
                match_value='dec', invert=True,
            ),
            res,
        )

    def test_parse_header_query_matcher__full__disallow_ignore(self) -> None:
        """Test parse_header_query_matcher with default values."""
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'query-parameters': [{
                            'parameter-name': 'qd1',
                            'match-type': 'exact',
                            'value': 'abc',
                            'case-sensitive': False,
                            'invert': True,
                        }],
                    })],
                })],
            })],
        })
        res = gateway.parse_header_query_matcher(
            discovery_map['namespaces'][0]['service-colors'][0]['routes'][0]['query-parameters'][0],
            'parameter-name',
            False,
        )
        self.assertEqual(
            common.HeaderQueryMatcher(
                name='qd1', match_type='exact', case_sensitive=False,
                match_value='abc', invert=False,
            ),
            res,
        )

    def test_get_service_color_cluster_name(self) -> None:
        """Test get_service_color_cluster_name"""
        res = gateway.get_service_color_cluster_name('s1', 'c1')
        self.assertEqual('c-s1-c1', res)

    def test_get_service_color_instance__ipv4(self) -> None:
        """Test get_service_color_instance with ipv4 address"""
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [_mk_service_color({
                    'instances': [
                        {'ipv4': '127.0.0.1', 'port': 12},
                    ],
                })],
            })],
        })
        res = gateway.get_service_color_instance(
            discovery_map['namespaces'][0]['service-colors'][0]['instances'][0],
        )
        self.assertEqual(
            common.EnvoyClusterEndpoint('127.0.0.1', 12, 'ipv4'),
            res,
        )

    def test_get_service_color_instance__ipv6(self) -> None:
        """Test get_service_color_instance with ipv6 address"""
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [_mk_service_color({
                    'instances': [
                        {'ipv6': '::1', 'port': 13},
                    ],
                })],
            })],
        })
        res = gateway.get_service_color_instance(
            discovery_map['namespaces'][0]['service-colors'][0]['instances'][0],
        )
        self.assertEqual(
            common.EnvoyClusterEndpoint('::1', 13, 'ipv6'),
            res,
        )

    def test_get_service_color_instance__hostname(self) -> None:
        """Test get_service_color_instance with hostname address"""
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [_mk_service_color({
                    'instances': [
                        {'hostname': 'host.docker.internal', 'port': 14},
                    ],
                })],
            })],
        })
        res = gateway.get_service_color_instance(
            discovery_map['namespaces'][0]['service-colors'][0]['instances'][0],
        )
        self.assertEqual(
            common.EnvoyClusterEndpoint('host.docker.internal', 14, 'hostname'),
            res,
        )

    def test_find_namespace_services__not_present(self) -> None:
        """Test find_namespace_services with namespace not present"""
        discovery_map = _mk_doc({})
        res = gateway.find_namespace_services(
            discovery_map,
            'n1'
        )
        self.assertIsNone(res)

    def test_find_namespace_services__present(self) -> None:
        """
        Test find_namespace_services with namespace present plus another, non-matching namespace.
        """
        discovery_map = _mk_doc({
            'namespaces': [
                _mk_namespace({
                    'namespace': 'n2',
                    'network-id': 'nk2',
                    'service-colors': [
                        _mk_service_color({'service': 'wrong', 'color': 'also wrong'}),
                    ],
                }),
                _mk_namespace({
                    'namespace': 'n1',
                    'network-id': 'nk1',
                    'service-colors': [
                        _mk_service_color({'service': 's1', 'color': 'c1'}),
                    ],
                }),
            ],
        })
        res = gateway.find_namespace_services(
            discovery_map,
            'n1',
        )
        self.assertIsNotNone(res)
        assert res is not None  # mypy requirement
        network_id, service_colors = res
        self.assertEqual('nk1', network_id)
        self.assertEqual(
            [_mk_service_color({'service': 's1', 'color': 'c1'})],
            service_colors,
        )


# ---------------------------------------------------------------------------
# discovery-map data construction helpers.
# The main entry, `mk_doc`, performs the validate.

def _mk_doc(defaults: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'version': 'v1',
        'namespaces': [],
    }
    ret.update(defaults)
    validate_discovery_map(ret)
    return ret


def _mk_namespace(defaults: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'namespace': 'n1',
        'network-id': 'nk1',
        'gateways': {'instances': [], 'prefer-gateway': False},
        'service-colors': [],
    }
    ret.update(defaults)
    return ret


def _mk_service_color(defaults: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'service': 's', 'color': 'c', 'routes': [], 'namespace-egress': [], 'instances': [],
    }
    ret.update(defaults)
    return ret


def _mk_route(defaults: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'path-match': {'match-type': 'exact', 'value': '/'},
        'weight': 1,
        'namespace-protection': [],
        'default-protection': 'public',
    }
    ret.update(defaults)
    return ret
