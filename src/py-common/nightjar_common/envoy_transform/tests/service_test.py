
"""Test the service module"""

from typing import Dict, Any
import unittest
from .. import service
from ...validation import validate_discovery_map


class ServiceTest(unittest.TestCase):
    """Test the service functions"""

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
        res = service.create_nonlocal_service_cluster_name('n1', 's1', 'c1')
        self.assertEqual('remote-n1-s1-c1', res)

    def test_create_nonlocal_gateway_cluster_name(self) -> None:
        """Test the create_nonlocal_gateway_cluster_name function"""
        res = service.create_nonlocal_gateway_cluster_name('n1')
        self.assertEqual('remote-n1-gateway', res)

    def test_create_local_cluster_name(self) -> None:
        """Test the create_local_cluster_name function"""
        res = service.create_local_cluster_name('s1', 'c1')
        self.assertEqual('local-s1-c1', res)


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
        'service': 's', 'color': 'c', 'routes': [], 'namespace-egress': [], 'instances': [],
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
