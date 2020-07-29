
"""
Test the common module.
"""

# These tests include heavy checks for equality, which pylint warns about.
# pylint: disable=R0124,C0121

from typing import Dict, Any
import unittest
from .. import common
from ...validation import validate_proxy_input


class HeaderQueryMatcherTest(unittest.TestCase):
    """Test the HeaderQueryMatcher class"""

    def test_get_context(self) -> None:
        """Test the get_context call, and ensure it passes validation."""
        query_header = common.HeaderQueryMatcher(
            name='h1', match_type='exact', case_sensitive=True, match_value='v1', invert=False,
        )
        query_header_doc = query_header.get_context()
        expected = {
            'name': 'h1',
            'match': 'v1',
            'is_exact_match': True,
            'is_regex_match': False,
            'is_present_match': False,
            'is_prefix_match': False,
            'is_suffix_match': False,
            'invert_match': False,
            'case_sensitive': True,
        }
        self.assertEqual(expected, query_header_doc)
        # Throw in an extra, tangentially related check...
        self.assertEqual(repr(expected), repr(query_header))
        validate_proxy_input(
            _mk_pi_doc({
                'listeners': [_mk_pi_listener({'routes': [_mk_pi_route({
                    'header_filters': [query_header_doc],
                })]})],
            })
        )

    def test_hashing_functions(self) -> None:
        """Test the eq, ne, and hash functions."""
        hqm1 = common.HeaderQueryMatcher('q1', 'exact', True, 'x', False)
        hqm1b = common.HeaderQueryMatcher('q1', 'exact', True, 'x', False)
        hqm2 = common.HeaderQueryMatcher('q1', 'exact', True, 'x', True)
        hqm3 = common.HeaderQueryMatcher('q1', 'exact', True, 'y', False)
        hqm4 = common.HeaderQueryMatcher('q1', 'exact', False, 'x', False)
        hqm5 = common.HeaderQueryMatcher('q1', 'regex', True, 'x', False)
        hqm6 = common.HeaderQueryMatcher('q2', 'exact', True, 'x', False)

        self.assertTrue(hqm1 == hqm1)
        self.assertTrue(hqm1 == hqm1b)
        self.assertFalse(hqm1 != hqm1)
        self.assertFalse(hqm1 != hqm1b)
        self.assertEqual(hash(hqm1), hash(hqm1))
        self.assertEqual(hash(hqm1), hash(hqm1b))

        self.assertFalse(hqm1 == hqm2)
        self.assertTrue(hqm1 != hqm2)

        self.assertFalse(hqm1 == hqm3)
        self.assertTrue(hqm1 != hqm3)

        self.assertFalse(hqm1 == hqm4)
        self.assertTrue(hqm1 != hqm4)

        self.assertFalse(hqm1 == hqm5)
        self.assertTrue(hqm1 != hqm5)

        self.assertFalse(hqm1 == hqm6)
        self.assertTrue(hqm1 != hqm6)

        self.assertFalse(hqm1 == 'blah')
        self.assertFalse(hqm1 == None)
        self.assertTrue(hqm1 != 'blah')
        self.assertTrue(hqm1 != None)


class RoutePathMatcherTest(unittest.TestCase):
    """Test the RoutePathMatcher class."""

    def test_prefix(self) -> None:
        """Test with prefix matching"""
        rpm = common.RoutePathMatcher('/p/1', 'prefix', True)
        self.assertTrue(rpm.is_prefix)
        self.assertFalse(rpm.is_regex)
        self.assertFalse(rpm.is_exact)
        self.assertTrue(rpm.case_sensitive)

    def test_exact(self) -> None:
        """Test with prefix matching"""
        rpm = common.RoutePathMatcher('/p/1', 'exact', True)
        self.assertFalse(rpm.is_prefix)
        self.assertFalse(rpm.is_regex)
        self.assertTrue(rpm.is_exact)
        self.assertTrue(rpm.case_sensitive)

    def test_regex(self) -> None:
        """Test with prefix matching"""
        rpm = common.RoutePathMatcher('/p/1', 'regex', False)
        self.assertFalse(rpm.is_prefix)
        self.assertTrue(rpm.is_regex)
        self.assertFalse(rpm.is_exact)
        self.assertFalse(rpm.case_sensitive)

    def test_hashing_functions(self) -> None:
        """Test the eq, ne, and hash functions."""
        rpm1 = common.RoutePathMatcher('q1', 'exact', True)
        rpm1b = common.RoutePathMatcher('q1', 'exact', True)
        rpm2 = common.RoutePathMatcher('q1', 'prefix', True)
        rpm3 = common.RoutePathMatcher('q1', 'regex', True)
        rpm4 = common.RoutePathMatcher('q1', 'exact', False)
        rpm5 = common.RoutePathMatcher('q2', 'exact', True)

        self.assertTrue(rpm1 == rpm1)
        self.assertTrue(rpm1 == rpm1b)
        self.assertFalse(rpm1 != rpm1)
        self.assertFalse(rpm1 != rpm1b)
        self.assertEqual(hash(rpm1), hash(rpm1))
        self.assertEqual(hash(rpm1), hash(rpm1b))

        self.assertFalse(rpm1 == rpm2)
        self.assertTrue(rpm1 != rpm2)

        self.assertFalse(rpm1 == rpm3)
        self.assertTrue(rpm1 != rpm3)

        self.assertFalse(rpm1 == rpm4)
        self.assertTrue(rpm1 != rpm4)

        self.assertFalse(rpm1 == rpm5)
        self.assertTrue(rpm1 != rpm5)

        self.assertFalse(rpm1 == 'blah')
        self.assertFalse(rpm1 == None)
        self.assertTrue(rpm1 != 'blah')
        self.assertTrue(rpm1 != None)


class RouteMatcherTest(unittest.TestCase):
    """Test the RouteMatcher class"""

    def test_get_context__bare(self) -> None:
        """Test the get_context, and validate it."""
        route_matcher = common.RouteMatcher(
            path_matcher=common.RoutePathMatcher('/p/2', 'exact', True),
            header_matchers=[], query_matchers=[],
        )
        rm_doc = route_matcher.get_context()
        expected = {
            'route_path': '/p/2',
            'path_is_prefix': False,
            'path_is_exact': True,
            'path_is_regex': False,
            'path_is_case_sensitive': True,
            'has_header_filters': False,
            'header_filters': [],
            'has_query_filters': False,
            'query_filters': [],
        }
        self.assertEqual(expected, rm_doc)
        # Throw in an extra, tangentially related check...
        self.assertEqual(repr(expected), repr(rm_doc))
        validate_proxy_input(
            _mk_pi_doc({
                'listeners': [_mk_pi_listener({'routes': [_mk_pi_route(rm_doc)]})],
            })
        )

    def test_hashing_functions(self) -> None:
        """Test the eq, ne, and hash functions."""
        rm1 = common.RouteMatcher(
            common.RoutePathMatcher('/p1', 'exact', True),
            [
                # We're not testing the equality functionality of the matchers,
                # but that values have their equality called.
                common.HeaderQueryMatcher('n1', 'exact', True, 'x', False),
                common.HeaderQueryMatcher('n2', 'regex', False, 'y', True),
            ],
            [
                common.HeaderQueryMatcher('n3', 'prefix', False, 'a', True),
                common.HeaderQueryMatcher('n4', 'suffix', False, 'b', False),
            ],
        )
        rm1b = common.RouteMatcher(rm1.path_matcher, rm1.header_matchers, rm1.query_matchers)
        rm2 = common.RouteMatcher(
            rm1.path_matcher, [rm1.header_matchers[1], rm1.header_matchers[0]], rm1.query_matchers,
        )
        rm3 = common.RouteMatcher(
            rm1.path_matcher, rm1.header_matchers, [rm1.query_matchers[1], rm1.query_matchers[0]],
        )
        rm4 = common.RouteMatcher(
            common.RoutePathMatcher('/p1', 'regex', False),
            rm1.header_matchers, rm1.query_matchers,
        )
        rm5 = common.RouteMatcher(rm1.path_matcher, rm1.header_matchers, [])
        rm6 = common.RouteMatcher(rm1.path_matcher, [], rm1.query_matchers)

        self.assertTrue(rm1 == rm1)
        self.assertTrue(rm1 == rm1b)
        self.assertFalse(rm1 != rm1)
        self.assertFalse(rm1 != rm1b)
        self.assertEqual(hash(rm1), hash(rm1))
        self.assertEqual(hash(rm1), hash(rm1b))

        # Just slide it in here...
        self.assertEqual(repr(rm1), repr(rm1b))

        # Ordering of filters is not important?
        self.assertTrue(rm1 == rm2)
        self.assertFalse(rm1 != rm2)

        self.assertTrue(rm1 == rm3)
        self.assertFalse(rm1 != rm3)

        self.assertFalse(rm1 == rm4)
        self.assertTrue(rm1 != rm4)

        self.assertFalse(rm1 == rm5)
        self.assertTrue(rm1 != rm5)

        self.assertFalse(rm1 == rm6)
        self.assertTrue(rm1 != rm6)

        self.assertFalse(rm1 == 'blah')
        self.assertFalse(rm1 == None)
        self.assertTrue(rm1 != 'blah')
        self.assertTrue(rm1 != None)


class EnvoyRouteTest(unittest.TestCase):
    """Test the EnvoyRoute class"""

    def test_props(self) -> None:
        """Test the property methods."""
        matcher = common.RouteMatcher(common.RoutePathMatcher('/', 'exact', True), [], [])
        route = common.EnvoyRoute(matcher=matcher, cluster_weights={'c1': 2, 'c2': 6})
        self.assertEqual(
            {'c1': 2, 'c2': 6},
            route.cluster_weights,
        )
        self.assertIs(
            matcher,
            route.matcher,
        )
        self.assertTrue(route.is_valid())
        self.assertEqual(8, route.total_weight)

    def test_invalid(self) -> None:
        """Test when the route is invalid."""
        route = common.EnvoyRoute(
            common.RouteMatcher(common.RoutePathMatcher('/', 'exact', True), [], []),
            {'c1': 2, 'c2': -6},
        )
        self.assertFalse(route.is_valid())

    def test_context__empty(self) -> None:
        """Test get_context with no clusters"""
        route = common.EnvoyRoute(
            common.RouteMatcher(common.RoutePathMatcher('/', 'exact', True), [], []),
            {},
        )
        self.assertIsNone(route.get_context())

    def test_context(self) -> None:
        """Test get_context"""
        route = common.EnvoyRoute(
            common.RouteMatcher(common.RoutePathMatcher('/', 'exact', True), [], []),
            {'c1': 2, 'c2': 6},
        )
        full_doc = _mk_pi_doc({
            'listeners': [_mk_pi_listener({
                'routes': [route.get_context()],
            })],
        })
        validate_proxy_input(full_doc)
        self.assertEqual(
            {
                'route_path': '/',
                'path_is_exact': True,
                'path_is_regex': False,
                'path_is_prefix': False,
                'path_is_case_sensitive': True,
                'has_header_filters': False,
                'header_filters': [],
                'has_query_filters': False,
                'query_filters': [],
                'has_one_cluster': False,
                'has_many_clusters': True,
                'clusters': [
                    {'cluster_name': 'c1', 'route_weight': 2},
                    {'cluster_name': 'c2', 'route_weight': 6},
                ],
                'total_cluster_weight': 8,
            },
            route.get_context(),
        )


class EnvoyListenerTest(unittest.TestCase):
    """Test the EnvoyListener class."""

    def test_invalid(self) -> None:
        """Test an invalid listener."""
        listener = common.EnvoyListener(-1, [])
        self.assertFalse(listener.is_valid())
        listener = common.EnvoyListener(None, [])
        self.assertTrue(listener.is_valid())

    def test_get_route_contexts__no_valid_route(self) -> None:
        """Test get_route_contexts with no valid route."""
        listener = common.EnvoyListener(10, [
            common.EnvoyRoute(
                common.RouteMatcher(common.RoutePathMatcher('/', 'exact', True), [], []),
                {},
            ),
        ])
        self.assertEqual(
            [],
            listener.get_route_contexts(),
        )

    def test_get_context__with_port(self) -> None:
        """Test get_context"""
        listener = common.EnvoyListener(10, [
            common.EnvoyRoute(
                common.RouteMatcher(common.RoutePathMatcher('/', 'exact', True), [], []),
                {'c1': 2, 'c2': 6},
            ),
        ])
        full_doc = _mk_pi_doc({'listeners': [listener.get_context()]})
        validate_proxy_input(full_doc)
        self.assertEqual(
            {
                'has_mesh_port': True,
                'mesh_port': 10,
                # Don't need to test the route context; it's tested above
                'routes': [listener.routes[0].get_context()],
            },
            listener.get_context(),
        )

    def test_get_context__without_port(self) -> None:
        """Test get_context"""
        listener = common.EnvoyListener(None, [
            common.EnvoyRoute(
                common.RouteMatcher(common.RoutePathMatcher('/', 'exact', True), [], []),
                {'c1': 2, 'c2': 6},
            ),
        ])
        full_doc = _mk_pi_doc({'listeners': [listener.get_context()]})
        validate_proxy_input(full_doc)
        self.assertEqual(
            {
                'has_mesh_port': False,
                'mesh_port': None,
                # Don't need to test the route context; it's tested above
                'routes': [listener.routes[0].get_context()],
            },
            listener.get_context(),
        )


class EnvoyClusterEndpointTest(unittest.TestCase):
    """Test the EnvoyClusterEndpoint class"""

    def test_validity(self) -> None:
        """Test the is_valid call"""
        endpoint = common.EnvoyClusterEndpoint('1.2.3.4', -1, 'ipv4')
        self.assertFalse(endpoint.is_valid())
        endpoint = common.EnvoyClusterEndpoint('4.3.2.1', 2, 'ipv4')
        self.assertTrue(endpoint.is_valid())

    def test_hash_methods(self) -> None:
        """Test the hash methods."""
        ep1 = common.EnvoyClusterEndpoint('1.2.3.4', 2, 'ipv4')
        ep1b = common.EnvoyClusterEndpoint('1.2.3.4', 2, 'ipv4')
        ep2 = common.EnvoyClusterEndpoint('1.2.3.4', 2, 'ipv6')
        ep3 = common.EnvoyClusterEndpoint('1.2.3.4', 3, 'ipv4')
        ep4 = common.EnvoyClusterEndpoint('1.2.3.5', 2, 'ipv4')

        self.assertTrue(ep1 == ep1)
        self.assertTrue(ep1 == ep1b)
        self.assertFalse(ep1 != ep1)
        self.assertFalse(ep1 != ep1b)
        self.assertEqual(hash(ep1), hash(ep1))
        self.assertEqual(hash(ep1), hash(ep1b))

        self.assertFalse(ep1 == ep2)
        self.assertTrue(ep1 != ep2)

        self.assertFalse(ep1 == ep3)
        self.assertTrue(ep1 != ep3)

        self.assertFalse(ep1 == ep4)
        self.assertTrue(ep1 != ep4)

        self.assertFalse(ep1 == 'blah')
        self.assertFalse(ep1 == None)
        self.assertTrue(ep1 != 'blah')
        self.assertTrue(ep1 != None)


class EnvoyClusterTest(unittest.TestCase):
    """Test the EnvoyCluster class"""

    def test_validity(self) -> None:
        """Test the is_valid method"""
        cluster = common.EnvoyCluster('c1', False, [])
        self.assertTrue(cluster.is_valid())
        cluster = common.EnvoyCluster('c1', False, [
            common.EnvoyClusterEndpoint('1.2.3.4', -1, 'ipv4'),
        ])
        self.assertFalse(cluster.is_valid())

    def test_endpoint_count(self) -> None:
        """Test the endpoint_count method"""
        cluster = common.EnvoyCluster('c1', False, [])
        self.assertEqual(0, cluster.endpoint_count())
        cluster = common.EnvoyCluster('c1', False, [
            common.EnvoyClusterEndpoint('1.2.3.4', -1, 'ipv4'),
            common.EnvoyClusterEndpoint('1.2.3.4', -1, 'ipv6'),
        ])
        self.assertEqual(2, cluster.endpoint_count())

    def test_get_context__no_instances(self) -> None:
        """Test the get_context with no instances."""
        cluster = common.EnvoyCluster('c1', False, [])
        full_doc = _mk_pi_doc({'clusters': [cluster.get_context()]})
        validate_proxy_input(full_doc)
        self.assertEqual(
            {'name': 'c1', 'uses_http2': False, 'endpoints': []},
            cluster.get_context(),
        )

    def test_get_context__instances(self) -> None:
        """Test the get_context with no instances."""
        cluster = common.EnvoyCluster('c1', True, [
            common.EnvoyClusterEndpoint('1.2.3.4', 12, 'ipv4'),
        ])
        full_doc = _mk_pi_doc({'clusters': [cluster.get_context()]})
        validate_proxy_input(full_doc)
        self.assertEqual(
            {'name': 'c1', 'uses_http2': True, 'endpoints': [{
                'ipv4': '1.2.3.4', 'port': 12,
            }]},
            cluster.get_context(),
        )


class EnvoyConfigTest(unittest.TestCase):
    """Test the EnvoyConfig class"""

    def test_validity(self) -> None:
        """Test different forms of validity."""
        valid_listener = common.EnvoyListener(None, [])
        invalid_listener = common.EnvoyListener(-1, [])
        valid_cluster = common.EnvoyCluster('c1', False, [])
        invalid_cluster = common.EnvoyCluster('c1', False, [
            common.EnvoyClusterEndpoint('1.2.3.4', -1, 'ipv4'),
        ])
        self.assertFalse(common.EnvoyConfig([], []).is_valid())
        self.assertTrue(common.EnvoyConfig([valid_listener], [valid_cluster]).is_valid())
        self.assertFalse(common.EnvoyConfig([invalid_listener], [invalid_cluster]).is_valid())
        self.assertFalse(common.EnvoyConfig([valid_listener], [invalid_cluster]).is_valid())
        self.assertFalse(common.EnvoyConfig([invalid_listener], [valid_cluster]).is_valid())

    def test_get_context(self) -> None:
        """Test that the context is valid."""
        config = common.EnvoyConfig(
            [common.EnvoyListener(None, [])],
            [common.EnvoyCluster('c1', False, [
                # Include a cluster...
                common.EnvoyClusterEndpoint('a.b.c', 2, 'hostname'),
            ])],
        )
        base_context_1 = config.get_context('n1', 's1', 1)
        full_context_1 = dict(base_context_1)
        full_context_1['version'] = 'v1'
        base_context_none = config.get_context('n1', 's1', None)
        full_context_none = dict(base_context_none)
        full_context_none['version'] = 'v1'
        validate_proxy_input(full_context_1)
        validate_proxy_input(full_context_none)
        self.assertEqual(
            {
                'network_name': 'n1',
                'service_member': 's1',
                'has_admin_port': True,
                'admin_port': 1,
                'listeners': [config.listeners[0].get_context()],
                'has_clusters': True,
                'clusters': [config.clusters[0].get_context()],
            },
            base_context_1,
        )


class EnvoyConfigContextTest(unittest.TestCase):
    """Test the EnvoyConfigContext class"""

    def test_get_context(self) -> None:
        """Test the get_context method"""
        config_context = common.EnvoyConfigContext(
            common.EnvoyConfig(
                [common.EnvoyListener(None, [])],
                [common.EnvoyCluster('c1', False, [
                    # Include a cluster...
                    common.EnvoyClusterEndpoint('a.b.c', 2, 'hostname'),
                ])],
            ),
            'nk1', 's1', 12,
        )
        context = config_context.get_context()
        validate_proxy_input(context)
        self.assertEqual(
            {
                'version': 'v1',
                'network_name': 'nk1',
                'service_member': 's1',
                'has_admin_port': True,
                'admin_port': 12,
                'listeners': [config_context.config.listeners[0].get_context()],
                'has_clusters': True,
                'clusters': [config_context.config.clusters[0].get_context()],
            },
            context,
        )


class CommonFunctionTest(unittest.TestCase):
    """Test the functions in the module"""

    def test_is_protocol_http2(self) -> None:
        """Test is_protocol_http2 function"""
        self.assertTrue(common.is_protocol_http2('HTTP2'))
        self.assertTrue(common.is_protocol_http2('http2'))
        self.assertTrue(common.is_protocol_http2('Http2'))
        self.assertFalse(common.is_protocol_http2('http3'))
        self.assertFalse(common.is_protocol_http2('http1.1'))
        self.assertFalse(common.is_protocol_http2(None))



# ---------------------------------------------------------------------------
# proxy-input-schema document creators.

def _mk_pi_doc(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'version': 'v1',
        'network_name': 'nk1',
        'service_member': 's1-c1',
        'has_admin_port': True,
        'admin_port': 10,
        'listeners': [],
        'has_clusters': False,
        'clusters': [],
    }
    ret.update(overrides)
    return ret


def _mk_pi_listener(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'has_mesh_port': True,
        'mesh_port': 20,
        'routes': [],
    }
    ret.update(overrides)
    return ret


def _mk_pi_route(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'route_path': '/',
        'path_is_prefix': False,
        'path_is_exact': True,
        'path_is_regex': False,
        'path_is_case_sensitive': True,
        'has_header_filters': False,
        'header_filters': [],
        'has_query_filters': False,
        'query_filters': [],
        'has_one_cluster': False,
        'has_many_clusters': False,
        'total_cluster_weight': 0,
        'clusters': [],
    }
    ret.update(overrides)
    return ret
