
"""Test the service module"""

# pylint: disable=C0302

from typing import Dict, Any
import unittest
from .. import service, common
from ...validation import validate_discovery_map


class ServiceTest(unittest.TestCase):  # pylint: disable=R0904
    """Test the service functions."""

    def test_create_service_color_proxy_input__no_namespace(self) -> None:
        """Test create_service_color_proxy_input with no matching namespace."""
        res = service.create_service_color_proxy_input(
            _mk_doc({}),
            'n1', 's', 'c', 160, 170,
        )
        self.assertEqual(1, res)

    def test_create_service_color_proxy_input__no_clusters(self) -> None:
        """Test create_service_color_proxy_input with no matching namespace."""
        res = service.create_service_color_proxy_input(
            _mk_doc({'namespaces': [_mk_namespace({})]}),
            'n1', 's', 'c', 160, 170,
        )
        self.assertEqual(2, res)

    def test_create_service_color_proxy_input__minimal(self) -> None:
        """Test create_service_color_proxy_input with no matching namespace."""
        res = service.create_service_color_proxy_input(
            _mk_doc({'namespaces': [_mk_namespace({'service-colors': [_mk_service_color({})]})]}),
            'n1', 's', 'c', 160, 170,
        )
        self.assertEqual({
            'schema-version': 'v1',
            'network_name': 'nk1',
            'service_member': 's-c',
            'has_admin_port': True,
            'admin_port': 170,
            'has_clusters': False,
            'clusters': [],
            'listeners': [{'has_mesh_port': True, 'mesh_port': 160, 'routes': []}],
        }, res)

    def test_create_clusters__no_local_services(self) -> None:
        """Test create_clusters with no local services."""
        res = service.create_clusters('n1', 's1', 'c1', _mk_doc({}))
        self.assertIsNone(res)

    def test_create_clusters__no_matching_services(self) -> None:
        """Test create_clusters with no mathing services."""
        res = service.create_clusters('n1', 's1', 'c1', _mk_doc({
            'namespaces': [_mk_namespace({'service-colors': [_mk_service_color({})]})],
        }))
        self.assertIsNone(res)

    def test_create_clusters__local_and_nonlocal(self) -> None:
        """Test create_nonlocal_namespace_clusters with no non-local namespaces."""
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({
                'namespace': 'n1',
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/c/1'},
                    })],
                    'instances': [{'ipv4': '1.2.3.4', 'port': 12}],
                    'namespace-egress': [{
                        'namespace': 'n2',
                        'interface': {'ipv4': '127.0.0.1', 'port': 100},
                    }],
                })],
            }),
            _mk_namespace({
                'namespace': 'n2',
                'gateways': {
                    'prefer-gateway': False,
                    'protocol': 'HTTP2',
                    'instances': [{'ipv6': '::3', 'port': 90}],
                },
                'service-colors': [_mk_service_color({
                    'service': 'rs', 'color': 'rc',
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/r/1'},
                        'default-access': True,
                    })],
                    'instances': [{'ipv4': '123.45.67.89', 'port': 990}],
                })],
            }),
        ]})
        res = service.create_clusters('n1', 's', 'c', discovery_map)
        self.assertIsNotNone(res)
        assert res is not None  # mypy requirement
        self.assertEqual([
            {
                'name': 'local-s-c-1',
                'endpoints': [{'host': '1.2.3.4', 'port': 12}],
                'hosts_are_hostname': False,
                'hosts_are_ipv4': True,
                'hosts_are_ipv6': False,
                'uses_http2': False,
            },
            {
                'name': 'remote-n2-rs-rc-1',
                'endpoints': [{'host': '123.45.67.89', 'port': 990}],
                'hosts_are_hostname': False,
                'hosts_are_ipv4': True,
                'hosts_are_ipv6': False,
                'uses_http2': False,
            },
        ], [ec.get_context() for ec in res])

    def test_create_local_namespace_clusters__no_services(self) -> None:
        """Test create_local_namespace_clusters with no services"""
        res = service.create_local_namespace_clusters([])
        self.assertEqual([], res)

    def test_create_local_namespace_clusters__no_service_instances(self) -> None:
        """Test create_local_namespace_clusters with no instances"""
        res = service.create_local_namespace_clusters([_mk_service_color({})])
        self.assertEqual([], res)

    def test_create_local_namespace_clusters__one_instance(self) -> None:
        """Test create_local_namespace_clusters with no instances"""
        res = service.create_local_namespace_clusters([_mk_service_color({
            'instances': [{'ipv4': '1.2.3.4', 'port': 123}],
        })])
        self.assertEqual(
            [{
                'name': 'local-s-c-1',
                'endpoints': [{'host': '1.2.3.4', 'port': 123}],
                'hosts_are_hostname': False,
                'hosts_are_ipv4': True,
                'hosts_are_ipv6': False,
                'uses_http2': False,
            }],
            [cl.get_context() for cl in res],
        )

    def test_create_nonlocal_namespace_clusters__no_nonlocal(self) -> None:
        """Test create_nonlocal_namespace_clusters with no non-local namespaces."""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({
            'namespace': 'n1', 'service-colors': [_mk_service_color({})],
        })]})
        res = service.create_nonlocal_namespace_clusters(
            'n1', discovery_map['namespaces'][0]['service-colors'][0], discovery_map,
        )
        self.assertEqual([], res)

    def test_create_nonlocal_namespace_clusters__nonlocal_no_gateways(self) -> None:
        """Test create_nonlocal_namespace_clusters with no non-local namespaces."""
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({
                'namespace': 'n1',
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/c/1'},
                    })],
                    'namespace-egress': [{
                        'namespace': 'n2',
                        'interface': {'ipv4': '127.0.0.1', 'port': 100},
                    }],
                })],
            }),
            _mk_namespace({
                'namespace': 'n2',
                'gateways': {
                    'prefer-gateway': False,
                    'protocol': 'HTTP2',
                    'instances': [{'ipv6': '::3', 'port': 90}],
                },
                'service-colors': [_mk_service_color({
                    'service': 'rs', 'color': 'rc',
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/r/1'},
                        'default-access': True,
                    })],
                    'instances': [{'ipv4': '123.45.67.89', 'port': 990}],
                })],
            }),
        ]})
        res = service.create_nonlocal_namespace_clusters(
            'n1', discovery_map['namespaces'][0]['service-colors'][0], discovery_map,
        )
        self.assertEqual([{
            'name': 'remote-n2-rs-rc-1',
            'endpoints': [{'host': '123.45.67.89', 'port': 990}],
            'hosts_are_hostname': False,
            'hosts_are_ipv4': True,
            'hosts_are_ipv6': False,
            'uses_http2': False,
        }], [ec.get_context() for ec in res])

    def test_create_nonlocal_namespace_clusters__nonlocal_gateways(self) -> None:
        """Test create_nonlocal_namespace_clusters with no non-local namespaces."""
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({
                'namespace': 'n1',
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/c/1'},
                    })],
                    'namespace-egress': [{
                        'namespace': 'n2',
                        'interface': {'ipv4': '127.0.0.1', 'port': 100},
                    }],
                })],
            }),
            _mk_namespace({
                'namespace': 'n2',
                'gateways': {
                    'prefer-gateway': True,
                    'protocol': 'HTTP2',
                    'instances': [{'ipv6': '::3', 'port': 90}],
                },
                'service-colors': [_mk_service_color({
                    'service': 'rs', 'color': 'rc',
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/r/1'},
                        'default-access': True,
                    })],
                    'instances': [{'ipv4': '123.45.67.89', 'port': 990}],
                })],
            }),
        ]})
        res = service.create_nonlocal_namespace_clusters(
            'n1', discovery_map['namespaces'][0]['service-colors'][0], discovery_map,
        )
        self.assertEqual([{
            'name': 'remote-n2-gateway',
            'endpoints': [{'host': '::3', 'port': 90}],
            'hosts_are_hostname': False,
            'hosts_are_ipv4': False,
            'hosts_are_ipv6': True,
            'uses_http2': True,
        }], [ec.get_context() for ec in res])

    def test_create_service_color_cluster__no_instances(self) -> None:
        """Test create_service_color_cluster with no instances"""
        res = service.create_service_color_cluster('cs', _mk_service_color({}))
        self.assertIsNone(res)

    def test_create_service_color_cluster__two_instances(self) -> None:
        """Test create_service_color_cluster with no instances"""
        res = service.create_service_color_cluster('cs', _mk_service_color({
            'instances': [
                {'hostname': 'xyz', 'port': 99},
                {'hostname': 'abc', 'port': 98},
            ],
        }))
        self.assertIsNotNone(res)
        assert res is not None  # mypy requirement
        self.assertEqual(
            {
                'name': 'cs',
                'endpoints': [{'host': 'xyz', 'port': 99}, {'host': 'abc', 'port': 98}],
                'hosts_are_hostname': True,
                'hosts_are_ipv4': False,
                'hosts_are_ipv6': False,
                'uses_http2': False,
            },
            res.get_context(),
        )

    def test_create_gateway_cluster__no_instances(self) -> None:
        """Test create_gateway_cluster with no instances"""
        res = service.create_gateway_cluster('c', {
            'protocol': 'HTTP2',
            'prefer-gateway': False,
            'instances': [],
        })
        self.assertIsNone(res)

    def test_create_gateway_cluster__two_instances(self) -> None:
        """Test create_gateway_cluster with no instances"""
        res = service.create_gateway_cluster('c', {
            'protocol': 'HTTP2',
            'prefer-gateway': False,
            'instances': [
                {'ipv4': '127.0.0.1', 'port': 12},
                {'ipv4': '99.0.0.9', 'port': 12},
            ],
        })
        self.assertIsNotNone(res)
        assert res is not None  # mypy requirement
        self.assertEqual(
            {
                'name': 'c',
                'uses_http2': True,
                'hosts_are_ipv6': False,
                'hosts_are_ipv4': True,
                'hosts_are_hostname': False,
                'endpoints': [
                    {'host': '127.0.0.1', 'port': 12},
                    {'host': '99.0.0.9', 'port': 12},
                ],
            },
            res.get_context(),
        )

    def test_create_route_listeners(self) -> None:
        """Test create_route_listeners with basic local and non-local routes."""
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({
                'namespace': 'n1',
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/c/1'},
                    })],
                    'namespace-egress': [{
                        'namespace': 'n2',
                        'interface': {'ipv4': '127.0.0.1', 'port': 100},
                    }],
                })],
            }),
            _mk_namespace({
                'namespace': 'n2',
                'gateways': {
                    'prefer-gateway': False,
                    'protocol': 'HTTP2',
                    'instances': [{'ipv6': '::3', 'port': 90}],
                },
                'service-colors': [_mk_service_color({
                    'service': 'rs', 'color': 'rc',
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/r/1'},
                    })],
                })],
            }),
        ]})
        res = service.create_route_listeners(900, 'n1', 's', 'c', discovery_map)
        self.assertEqual(
            [
                {
                    'has_mesh_port': True,
                    'mesh_port': 900,
                    'routes': [{
                        'route_path': '/c/1',
                        'clusters': [{
                            'cluster_name': 'local-s-c-1',
                            'route_weight': 1,
                        }],
                        'has_header_filters': False,
                        'header_filters': [],
                        'has_query_filters': False,
                        'query_filters': [],
                        'has_many_clusters': False,
                        'has_one_cluster': True,
                        'path_is_case_sensitive': True,
                        'path_is_exact': True,
                        'path_is_prefix': False,
                        'path_is_regex': False,
                        'total_cluster_weight': 1,
                    }],
                }, {
                    'has_mesh_port': True,
                    'mesh_port': 100,
                    'routes': [{
                        'route_path': '/r/1',
                        'clusters': [{
                            'cluster_name': 'remote-n2-rs-rc-1',
                            'route_weight': 1,
                        }],
                        'has_header_filters': False,
                        'header_filters': [],
                        'has_query_filters': False,
                        'query_filters': [],
                        'has_many_clusters': False,
                        'has_one_cluster': True,
                        'path_is_case_sensitive': True,
                        'path_is_exact': True,
                        'path_is_prefix': False,
                        'path_is_regex': False,
                        'total_cluster_weight': 1,
                    }],
                },
            ],
            [el.get_context() for el in res],
        )

    def test_create_local_route_listener__no_routes(self) -> None:
        """Test create_local_route_listener with no routes."""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({})]})
        res = service.create_local_route_listener(60, 'n1', discovery_map)
        self.assertEqual({
            'has_mesh_port': True, 'mesh_port': 60, 'routes': [],
        }, res.get_context())

    def test_create_local_route_listener__one_routes(self) -> None:
        """Test create_local_route_listener with one route."""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({
            'service-colors': [_mk_service_color({
                'routes': [_mk_route({
                    'path-match': {'match-type': 'exact', 'value': '/s/1'},
                })],
            })],
        })]})
        res = service.create_local_route_listener(60, 'n1', discovery_map)
        self.assertEqual({
            'has_mesh_port': True, 'mesh_port': 60, 'routes': [{
                'route_path': '/s/1',
                'clusters': [{'cluster_name': 'local-s-c-1', 'route_weight': 1}],
                'has_header_filters': False,
                'header_filters': [],
                'has_query_filters': False,
                'query_filters': [],
                'has_many_clusters': False,
                'has_one_cluster': True,
                'path_is_case_sensitive': True,
                'path_is_exact': True,
                'path_is_prefix': False,
                'path_is_regex': False,
                'total_cluster_weight': 1,
            }],
        }, res.get_context())

    def test_create_nonlocal_route_listeners__no_such_namespace(self) -> None:
        """Tests create_nonlocal_route_listeners with no given namespace"""
        discovery_map = _mk_doc({})
        res = service.create_nonlocal_route_listeners('n1', 's', 'c', discovery_map)
        self.assertEqual([], res)

    def test_create_nonlocal_route_listeners__no_service_colors(self) -> None:
        """Tests create_nonlocal_route_listeners with no service colors"""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({})]})
        res = service.create_nonlocal_route_listeners('n1', 's', 'c', discovery_map)
        self.assertEqual([], res)

    def test_create_nonlocal_route_listeners__no_matching_service_colors(self) -> None:
        """Tests create_nonlocal_route_listeners with no service colors"""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({
            'service-colors': [_mk_service_color({})],
        })]})
        res = service.create_nonlocal_route_listeners('n1', 's2', 'c2', discovery_map)
        self.assertEqual([], res)

    def test_create_nonlocal_route_listeners__no_nonlocal(self) -> None:
        """Tests create_nonlocal_route_listeners with no non-local namespaces"""
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({'service-colors': [_mk_service_color({})]}),
        ]})
        res = service.create_nonlocal_route_listeners('n1', 's', 'c', discovery_map)
        self.assertEqual([], res)

    def test_create_nonlocal_route_listeners__one_preferred_gateway(self) -> None:
        """Tests create_nonlocal_route_listeners with a non-local namespace,
        which prefers use of a gateway"""
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({
                'namespace': 'n1',
                'service-colors': [_mk_service_color({
                    'namespace-egress': [{
                        'namespace': 'n2',
                        'interface': {'ipv4': '127.0.0.1', 'port': 100},
                    }],
                })],
            }),
            _mk_namespace({
                'namespace': 'n2',
                'gateways': {
                    'prefer-gateway': True,
                    'protocol': 'HTTP2',
                    'instances': [{'ipv6': '::3', 'port': 90}],
                },
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/s/1'},
                    })],
                })],
            }),
        ]})
        res = service.create_nonlocal_route_listeners('n1', 's', 'c', discovery_map)
        self.assertEqual([{
            'has_mesh_port': True,
            'mesh_port': 100,
            'routes': [{
                # Routes to gateways are '/' always.
                'route_path': '/',
                'clusters': [{'cluster_name': 'remote-n2-gateway', 'route_weight': 1}],
                'has_header_filters': False,
                'header_filters': [],
                'has_query_filters': False,
                'query_filters': [],
                'has_many_clusters': False,
                'has_one_cluster': True,
                'path_is_case_sensitive': True,
                'path_is_exact': False,
                'path_is_prefix': True,
                'path_is_regex': False,
                'total_cluster_weight': 1,
            }],
        }], [c.get_context() for c in res])

    def test_create_nonlocal_route_listeners__one_service_direct(self) -> None:
        """Tests create_nonlocal_route_listeners with a non-local namespace,
        which prefers use of a gateway"""
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({
                'namespace': 'n1',
                'service-colors': [_mk_service_color({
                    'namespace-egress': [{
                        'namespace': 'n2',
                        'interface': {'ipv4': '127.0.0.1', 'port': 100},
                    }],
                })],
            }),
            _mk_namespace({
                'namespace': 'n2',
                'gateways': {
                    'prefer-gateway': False,
                    'protocol': 'HTTP2',
                    'instances': [{'ipv6': '::3', 'port': 90}],
                },
                'service-colors': [_mk_service_color({
                    'routes': [_mk_route({
                        'path-match': {'match-type': 'exact', 'value': '/s/1'},
                    })],
                })],
            }),
        ]})
        res = service.create_nonlocal_route_listeners('n1', 's', 'c', discovery_map)
        self.assertEqual([{
            'has_mesh_port': True,
            'mesh_port': 100,
            'routes': [{
                'route_path': '/s/1',
                'clusters': [{'cluster_name': 'remote-n2-s-c-1', 'route_weight': 1}],
                'has_header_filters': False,
                'header_filters': [],
                'has_query_filters': False,
                'query_filters': [],
                'has_many_clusters': False,
                'has_one_cluster': True,
                'path_is_case_sensitive': True,
                'path_is_exact': True,
                'path_is_prefix': False,
                'path_is_regex': False,
                'total_cluster_weight': 1,
            }],
        }], [c.get_context() for c in res])

    def test_create_remote_gateway_listener(self) -> None:
        """Test create_remote_gateway_listener"""
        listener = service.create_remote_gateway_listener('c1', {'port': 5})
        self.assertIsNotNone(listener)
        assert listener is not None  # mypy requirement
        self.assertEqual(
            {
                'has_mesh_port': True,
                'mesh_port': 5,
                'routes': [{
                    'clusters': [{'cluster_name': 'c1', 'route_weight': 1}],
                    'has_header_filters': False,
                    'has_many_clusters': False,
                    'has_one_cluster': True,
                    'has_query_filters': False,
                    'header_filters': [],
                    'path_is_case_sensitive': True,
                    'path_is_exact': False,
                    'path_is_prefix': True,
                    'path_is_regex': False,
                    'query_filters': [],
                    'route_path': '/',
                    'total_cluster_weight': 1,
                }],
            },
            listener.get_context(),
        )

    def test_create_remote_namespace_listener__no_services(self) -> None:
        """Test create_remote_namespace_listener with no services."""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({})]})
        listener = service.create_remote_namespace_listener(
            'n2', {'port': 2}, discovery_map['namespaces'][0],
        )
        self.assertIsNotNone(listener)
        assert listener is not None  # mypy requirement
        self.assertEqual(
            {'has_mesh_port': True, 'mesh_port': 2, 'routes': []},
            listener.get_context(),
        )

    def test_create_remote_namespace_listener__one_service(self) -> None:
        """Test create_remote_namespace_listener with no services."""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({
            'service-colors': [_mk_service_color({'routes': [_mk_route({
                'path-match': {'match-type': 'exact', 'value': '/a'},
            })]})],
        })]})
        listener = service.create_remote_namespace_listener(
            'n2', {'port': 2}, discovery_map['namespaces'][0],
        )
        self.assertIsNotNone(listener)
        assert listener is not None  # mypy requirement
        self.assertEqual(
            {'has_mesh_port': True, 'mesh_port': 2, 'routes': [{
                'clusters': [{'cluster_name': 'remote-n1-s-c-1', 'route_weight': 1}],
                'has_many_clusters': False,
                'has_one_cluster': True,
                'has_header_filters': False,
                'header_filters': [],
                'has_query_filters': False,
                'query_filters': [],
                'path_is_case_sensitive': True,
                'path_is_exact': True,
                'path_is_prefix': False,
                'path_is_regex': False,
                'route_path': '/a',
                'total_cluster_weight': 1,
            }]},
            listener.get_context(),
        )

    def test_can_local_namespace_access_remote__no_services(self) -> None:
        """Test can_local_namespace_access_remote with no services defined."""
        res = service.can_local_namespace_access_remote('n1', _mk_namespace({}))
        self.assertFalse(res)

    def test_can_local_namespace_access_remote__no_access(self) -> None:
        """Test can_local_namespace_access_remote with no remote access."""
        res = service.can_local_namespace_access_remote('n1', _mk_namespace({'service-colors': [
            _mk_service_color({'routes': [_mk_route({'default-access': False})]}),
        ]}))
        self.assertFalse(res)

    def test_can_local_namespace_access_remote__access(self) -> None:
        """Test can_local_namespace_access_remote with allowed remote access."""
        res = service.can_local_namespace_access_remote('n1', _mk_namespace({'service-colors': [
            _mk_service_color({'routes': [_mk_route({'default-access': True})]}),
        ]}))
        self.assertTrue(res)

    def test_find_namespace_service_colors__match(self) -> None:
        """Test find_namespace_service_colors with no matching namespace"""
        scl = [_mk_service_color({})]
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({
            'namespace': 'n1', 'service-colors': scl,
        })]})
        res = service.find_namespace_service_colors('n1', discovery_map)
        self.assertEqual(scl, res)

    def test_find_namespace_service_colors__no_namespace(self) -> None:
        """Test find_namespace_service_colors with no matching namespace"""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({'namespace': 'n1'})]})
        res = service.find_namespace_service_colors('n2', discovery_map)
        self.assertIsNone(res)

    def test_find_service_color__no_match(self) -> None:
        """Test find_service_color with no match."""
        scl = [_mk_service_color({'service': 'x', 'color': 'y'})]
        res = service.find_service_color('s', 'c', scl)
        self.assertIsNone(res)

    def test_find_service_color__partial(self) -> None:
        """Test find_service_color with partial matches."""
        scl = [_mk_service_color({'service': 'x', 'color': 'y'})]
        res = service.find_service_color('s', 'y', scl)
        self.assertIsNone(res)
        res = service.find_service_color('x', 'c', scl)
        self.assertIsNone(res)

    def test_find_service_color__first_match(self) -> None:
        """Test find_service_color with partial matches."""
        scl = [
            _mk_service_color({'service': 's', 'color': 'c', 'x': 'y'}),
            _mk_service_color({'service': 's', 'color': 'c', 'a': 'b'}),
        ]
        res = service.find_service_color('s', 'c', scl)
        self.assertEqual(scl[0], res)

    def test_find_nonlocal_namespaces__none(self) -> None:
        """Test find_nonlocal_namespaces with no non-local namespaces."""
        discovery_map = _mk_doc({'namespaces': [_mk_namespace({
            'service-colors': [_mk_service_color({})],
        })]})
        res = service.find_nonlocal_namespaces(
            discovery_map['namespaces'][0]['namespace'],
            discovery_map['namespaces'][0]['service-colors'][0],
            discovery_map,
        )
        self.assertEqual([], res)

    def test_find_nonlocal_namespaces__two(self) -> None:
        """Test find_nonlocal_namespaces with two non-local namespaces."""
        nl1 = _mk_namespace({'namespace': 'n2', 'service-colors': [_mk_service_color({
            'routes': [_mk_route({})],
        })]})
        nl2 = _mk_namespace({'namespace': 'n3', 'service-colors': [_mk_service_color({
            'routes': [_mk_route({})],
        })]})
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({
                'service-colors': [_mk_service_color({
                    'namespace-egress': [
                        {'namespace': 'n2', 'interface': {'ipv4': '127.0.0.1', 'port': 2}},
                        {'namespace': 'n3', 'interface': {'ipv4': '127.0.0.1', 'port': 2}},
                    ],
                })],
            }),
            nl1, nl2,
        ]})
        res = service.find_nonlocal_namespaces(
            discovery_map['namespaces'][0]['namespace'],
            discovery_map['namespaces'][0]['service-colors'][0],
            discovery_map,
        )
        self.assertEqual([nl1, nl2], res)

    def test_find_nonlocal_namespaces__some(self) -> None:
        """Test find_nonlocal_namespaces with two non-local namespaces, only one of which
        has an egress."""
        nl1 = _mk_namespace({'namespace': 'n2', 'service-colors': [_mk_service_color({
            'routes': [_mk_route({})],
        })]})
        nl2 = _mk_namespace({'namespace': 'n3', 'service-colors': [_mk_service_color({
            'routes': [_mk_route({})],
        })]})
        discovery_map = _mk_doc({'namespaces': [
            _mk_namespace({
                'service-colors': [_mk_service_color({
                    'namespace-egress': [
                        {'namespace': 'n2', 'interface': {'ipv4': '127.0.0.1', 'port': 2}},
                    ],
                })],
            }),
            nl1, nl2,
        ]})
        res = service.find_nonlocal_namespaces(
            discovery_map['namespaces'][0]['namespace'],
            discovery_map['namespaces'][0]['service-colors'][0],
            discovery_map,
        )
        self.assertEqual([nl1], res)

    def test_get_namespace_egress_instance__empty(self) -> None:
        """Test get_namespace_egress_instance with no matching namespace"""
        res = service.get_namespace_egress_instance('n2', _mk_service_color({
            'namespace-egress': [],
        }))
        self.assertEqual(None, res)

    def test_get_namespace_egress_instance__no_match(self) -> None:
        """Test get_namespace_egress_instance with no matching namespace"""
        res = service.get_namespace_egress_instance('n2', _mk_service_color({
            'namespace-egress': [{'namespace': 'x', 'interface': {'ipv4': '127.0.0.1', 'port': 2}}],
        }))
        self.assertEqual(None, res)

    def test_get_namespace_egress_instance__match(self) -> None:
        """Test get_namespace_egress_instance with no matching namespace"""
        egress = {'namespace': 'n2', 'interface': {'ipv4': '127.0.0.1', 'port': 2}}
        res = service.get_namespace_egress_instance('n2', _mk_service_color({
            'namespace-egress': [egress],
        }))
        self.assertEqual(egress['interface'], res)

    def test_group_service_colors_by_route__empty(self) -> None:
        """Test group_service_colors_by_route with no service colors."""
        res = service.group_service_colors_by_route([], None, service.create_local_cluster_name)
        self.assertEqual({}, res)

    def test_group_service_colors_by_route__several_services_one_public_route(self) -> None:
        """Test group_service_colors_by_route with no service colors."""
        route_1 = _mk_route({'path-match': {'match-type': 'prefix', 'value': '/a'}, 'weight': 2})
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [
                    _mk_service_color({
                        'color': 'blue',
                        'instances': [{'ipv6': '::1', 'port': 6}],
                        'routes': [route_1],
                    }),
                    _mk_service_color({
                        'color': 'blue', 'index': 2,
                        'instances': [{'ipv6': '::1', 'port': 8}],
                        'routes': [route_1],
                    }),
                    _mk_service_color({
                        'color': 'green',
                        'instances': [{'ipv6': '::2', 'port': 6}],
                        'routes': [route_1],
                    }),
                ],
            })],
        })
        res = service.group_service_colors_by_route(
            discovery_map['namespaces'][0]['service-colors'],
            None,
            service.create_local_cluster_name,
        )
        matched_route = common.RouteMatcher(common.RoutePathMatcher('/a', 'prefix', True), [], [])
        self.assertEqual(
            {
                matched_route: [
                    ('local-s-blue-1', {
                        'default-access': True,
                        'namespace-access': [],
                        'path-match': {'match-type': 'prefix', 'value': '/a'},
                        'weight': 2,
                    }),
                    ('local-s-blue-2', {
                        'default-access': True,
                        'namespace-access': [],
                        'path-match': {'match-type': 'prefix', 'value': '/a'},
                        'weight': 2,
                    }),
                    ('local-s-green-1', {
                        'default-access': True,
                        'namespace-access': [],
                        'path-match': {'match-type': 'prefix', 'value': '/a'},
                        'weight': 2,
                    }),
                ],
            },
            res,
        )

    def test_group_service_colors_by_route__private_remote(self) -> None:
        """Test group_service_colors_by_route with no service colors."""
        route_1 = _mk_route({
            'path-match': {'match-type': 'prefix', 'value': '/a'}, 'weight': 2,
            'namespace-access': [{'namespace': 'n1', 'access': False}],
        })
        discovery_map = _mk_doc({
            'namespaces': [_mk_namespace({
                'service-colors': [
                    _mk_service_color({
                        'color': 'blue',
                        'instances': [{'ipv6': '::1', 'port': 6}],
                        'routes': [route_1],
                    }),
                ],
            })],
        })
        res = service.group_service_colors_by_route(
            discovery_map['namespaces'][0]['service-colors'],
            'n1',
            service.create_local_cluster_name,
        )
        self.assertEqual({}, res)

    def test_get_route_matcher_key__defaults(self) -> None:
        """Test get_route_matcher_key, with as many default values as possible."""
        res = service.get_route_matcher_key(_mk_route({
            'path-match': {
                'match-type': 'foo',
                'value': '/bar',
            },
        }))
        self.assertEqual(
            common.RouteMatcher(
                common.RoutePathMatcher('/bar', 'foo', True),
                [], [],
            ),
            res,
        )

    def test_get_route_matcher_key__full(self) -> None:
        """Test get_route_matcher_key, with everything filled in."""
        res = service.get_route_matcher_key(_mk_route({
            'path-match': {
                'match-type': 'foo',
                'value': '/bar',
                'case-sensitive': False,
            },
            'headers': [{
                'header-name': 'boil',
                'match-type': 'tuna', 'case-sensitive': False,
                'value': 'melt', 'invert': True,
            }],
            'query-parameters': [{
                'parameter-name': 'curdle',
                'match-type': 'marlin', 'case-sensitive': False,
                'value': 'hook', 'invert': True,
            }],
        }))
        self.assertEqual(
            common.RouteMatcher(
                common.RoutePathMatcher('/bar', 'foo', False),
                [common.HeaderQueryMatcher('boil', 'tuna', False, 'melt', True)],
                [common.HeaderQueryMatcher('curdle', 'marlin', False, 'hook', False)],
            ),
            res,
        )

    def test_parse_header_query_matcher__allow_ignore__defaults(self) -> None:
        """Test parse_header_query_matcher with as many default values as possible,
        allowing ignores."""
        res = service.parse_header_query_matcher(
            {'name': 'abc', 'match-type': 'tuna'},
            'name',
            True,
        )
        self.assertEqual(
            common.HeaderQueryMatcher('abc', 'tuna', True, None, False),
            res,
        )

    def test_parse_header_query_matcher__allow_ignore__full(self) -> None:
        """Test parse_header_query_matcher with as many default values as possible,
        allowing ignores."""
        res = service.parse_header_query_matcher(
            {
                'name': 'abc', 'match-type': 'tuna', 'case-sensitive': False,
                'value': 'melt', 'invert': True,
            },
            'name',
            True,
        )
        self.assertEqual(
            common.HeaderQueryMatcher('abc', 'tuna', False, 'melt', True),
            res,
        )

    def test_parse_header_query_matcher__disallow_ignore__full(self) -> None:
        """Test parse_header_query_matcher with as many default values as possible,
        allowing ignores."""
        res = service.parse_header_query_matcher(
            {
                'name': 'abc', 'match-type': 'tuna', 'case-sensitive': False,
                'value': 'melt', 'invert': True,
            },
            'name',
            False,
        )
        self.assertEqual(
            common.HeaderQueryMatcher('abc', 'tuna', False, 'melt', False),
            res,
        )

    def test_can_local_namespace_access_route__no_namespace1(self) -> None:
        """Test can_local_namespace_access_route with no matching namespace"""
        route = _mk_route({
            'default-access': True,
        })
        res = service.can_local_namespace_access_route('n1', route)
        self.assertTrue(res)

    def test_can_local_namespace_access_route__no_namespace2(self) -> None:
        """Test can_local_namespace_access_route with no matching namespace"""
        route = _mk_route({
            'namespace-access': [{'namespace': 'n2', 'access': True}],
            'default-access': False,
        })
        res = service.can_local_namespace_access_route('n1', route)
        self.assertFalse(res)

    def test_can_local_namespace_access_route__with_namespace(self) -> None:
        """Test can_local_namespace_access_route with no matching namespace"""
        route = _mk_route({
            'namespace-access': [{'namespace': 'n1', 'access': True}],
            'default-access': False,
        })
        res = service.can_local_namespace_access_route('n1', route)
        self.assertTrue(res)

    def test_can_local_namespace_access_route__with_namespace_false(self) -> None:
        """Test can_local_namespace_access_route with no matching namespace"""
        route = _mk_route({
            'namespace-access': [{'namespace': 'n1', 'access': False}],
            'default-access': True,
        })
        res = service.can_local_namespace_access_route('n1', route)
        self.assertFalse(res)

    def test_find_namespace__none(self) -> None:
        """Test find_namespace with no namespaces"""
        discovery_map = _mk_doc({})
        res = service.find_namespace('n1', discovery_map)
        self.assertIsNone(res)

    def test_find_namespace(self) -> None:
        """Test find_namespace"""
        namespace = _mk_namespace({
            'namespace': 'n1',
        })
        discovery_map = _mk_doc({
            'namespaces': [namespace],
        })
        res = service.find_namespace('n1', discovery_map)
        self.assertEqual(namespace, res)

    def test_create_nonlocal_service_cluster_name(self) -> None:
        """Test the create_nonlocal_service_cluster_name function"""
        res = service.create_nonlocal_service_cluster_name('n1', 's1', 'c1', 100)
        self.assertEqual('remote-n1-s1-c1-100', res)

    def test_create_nonlocal_gateway_cluster_name(self) -> None:
        """Test the create_nonlocal_gateway_cluster_name function"""
        res = service.create_nonlocal_gateway_cluster_name('n1')
        self.assertEqual('remote-n1-gateway', res)

    def test_create_local_cluster_name(self) -> None:
        """Test the create_local_cluster_name function"""
        res = service.create_local_cluster_name('s1', 'c1', 65535)
        self.assertEqual('local-s1-c1-65535', res)


# ---------------------------------------------------------------------------
# discovery-map data construction helpers.
# The main entry, `mk_doc`, performs the validate.

def _mk_doc(defaults: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'schema-version': 'v1',
        'document-version': 'x',
        'namespaces': [],
    }
    ret.update(defaults)
    validate_discovery_map(ret)
    return ret


def _mk_namespace(defaults: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'namespace': 'n1',
        'network-id': 'nk1',
        'gateways': {'instances': [], 'prefer-gateway': False, 'protocol': 'http1.1'},
        'service-colors': [],
    }
    ret.update(defaults)
    return ret


def _mk_service_color(defaults: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'service': 's', 'color': 'c', 'index': 1,
        'routes': [], 'namespace-egress': [], 'instances': [],
    }
    ret.update(defaults)
    return ret


def _mk_route(defaults: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'path-match': {'match-type': 'exact', 'value': '/'},
        'weight': 1,
        'namespace-access': [],
        'default-access': True,
    }
    ret.update(defaults)
    return ret
