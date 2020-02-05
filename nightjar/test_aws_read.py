
import unittest
from datetime import datetime
from typing import Dict, List, Any
import boto3
import botocore.stub
generator = __import__('generate-envoy-proxy')


class TestDataRead(unittest.TestCase):
    def test_read_service_id(self) -> None:
        msd = MockServiceDiscovery()
        msd.mk_service(service_id='1234', name='a1234', namespace_id='xyz')
        with msd:
            msd.client.get_service(Id='1234')

    def test_read_service_id_not_exist(self) -> None:
        msd = MockServiceDiscovery()
        msd.mk_service_not_found('1234')
        with msd:
            msd.client.get_service(Id='1234')


class MockServiceDiscovery:
    services: List[Dict[str, Any]] = []

    def __init__(self) -> None:
        self.client = None
        self._client = boto3.client('servicediscovery')
        self.stubber = botocore.stub.Stubber(self._client)
        self.old_client = None

    def __enter__(self) -> None:
        self.client = self._client
        self.old_client = generator.CLIENTS.get('servicediscovery')
        generator.CLIENTS['servicediscovery'] = self._client
        return self.stubber.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.client = None
        if self.old_client is None:
            del generator.CLIENTS['servicediscovery']
        else:
            generator.CLIENTS['servicediscovery'] = self.old_client
            self.old_client = None
        return self.stubber.__exit__(exc_type, exc_val, exc_tb)

    def mk_service_not_found(self, service_id: str) -> None:
        self.stubber.add_client_error(
            'get_service',
            expected_params={'Id': service_id},
            service_error_code='ServiceNotFound'
        )

    def mk_service(self, service_id: str, name: str, namespace_id: str) -> None:
        self.stubber.add_response('get_service', {'Service': {
            'Id': service_id,
            'Arn': 'arn:blah:' + service_id,
            'Name': name,
            'NamespaceId': namespace_id,
            'Description': 'blah',
            'InstanceCount': 123,
            'DnsConfig': {
                'NamespaceId': namespace_id,
                'RoutingPolicy': 'WEIGHTED',
                'DnsRecords': [{'Type': 'SRV', 'TTL': 123}],
            },
            'HealthCheckConfig': {
                'Type': 'HTTP',
                'ResourcePath': '/',
                'FailureThreshold': 123,
            },
            'HealthCheckCustomConfig': {
                'FailureThreshold': 123
            },
            'CreateDate': datetime(2015, 1, 1),
            'CreatorRequestId': 'string',
        }}, {'Id': service_id})
