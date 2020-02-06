
import unittest
from datetime import datetime
from typing import Dict, List, Any
import boto3
import botocore.stub
import generate_template_input_data as generator


class TestDiscoveryServiceInstance(unittest.TestCase):
    """
    Validate DiscoveryServiceInstance can parse the data correctly.
    """

    def test_full_attributes(self) -> None:
        data = {
            generator.ATTR_AWS_INSTANCE_IPV4: '10.0.5.92',
            generator.ATTR_EC2_INSTANCE_ID: 'i-1234',
            generator.ATTR_AWS_INSTANCE_PORT: '9080',
            generator.ATTR_AWS_INIT_HEALTH_STATUS: 'UNHEALTHY',
            generator.ATTR_AVAILABILITY_ZONE: 'az-xyz',
            generator.ATTR_REGION: 'eu-west-2',
            generator.ATTR_ECS_CLUSTER_NAME: 'my-cluster',
            generator.ATTR_ECS_SERVICE_NAME: 'svc-abc',
            generator.ATTR_ECS_TASK_DEFINITION_FAMILY: 'my-family',
        }
        instance = generator.DiscoveryServiceInstance('id1', data)
        self.assertEqual(instance.attributes, data)
        self.assertEqual(instance.instance_id, 'id1')
        self.assertEqual(instance.port_str, '9080')
        self.assertEqual(instance.ipv4, '10.0.5.92')
        self.assertEqual(instance.ec2_instance_id, 'i-1234')

    def test_empty_attributes(self) -> None:
        instance = generator.DiscoveryServiceInstance('id2', {})
        self.assertEqual(instance.attributes, {})
        self.assertEqual(instance.instance_id, 'id2')
        self.assertEqual(instance.port_str, '0')
        self.assertEqual(instance.ipv4, None)
        self.assertEqual(instance.ec2_instance_id, None)


class TestDiscoveryServiceColorReadData(unittest.TestCase):
    """
    Validate DiscoveryServiceColor correctly reads data from the AWS service discovery
    service APIs, and handles error conditions.
    """

    def test_read_service_id(self) -> None:
        """
        Happy path read.  The service exists and has instances throughout the setup process.
        """
        msd = MockServiceDiscovery()
        msd.mk_service(service_id='1234', name='a1234', namespace_id='xyz')
        msd.mk_instances(service_id='1234', instance_attributes={
            # The special meta-data instance entry.
            generator.SERVICE_SETTINGS_INSTANCE_ID: {
                # Ignored stuff
                generator.ATTR_AWS_INSTANCE_IPV4: '0.0.0.0',
                generator.ATTR_EC2_INSTANCE_ID: 'i-1234',
                generator.ATTR_AWS_INSTANCE_PORT: '8080',
                generator.ATTR_AWS_INIT_HEALTH_STATUS: 'UNHEALTHY',
                generator.ATTR_AVAILABILITY_ZONE: 'az-xyz',
                generator.ATTR_REGION: 'eu-west-2',
                generator.ATTR_ECS_CLUSTER_NAME: 'my-cluster',
                generator.ATTR_ECS_SERVICE_NAME: 'svc-abc',
                generator.ATTR_ECS_TASK_DEFINITION_FAMILY: 'my-family',

                # Descriptive stuff
                generator.SERVICE_NAME_ATTRIBUTE_KEY: 'service-A1',
                generator.COLOR_NAME_ATTRIBUTE_KEY: 'puce',
                generator.USES_HTTP2_ATTRIBUTE_KEY: 'no',

                # Path/weight definitions
                '/path1': '10',
                '?/path2': '6',
                '/path3/path4': '8',
                '/path3/path5': '7',

                # An invalid weight should generate a warning + assign the value to '1`
                '/bad/weight': 'not-a-number',
            },
            '1234-5678': {
                # A custom instance, generated from an ECS task registration
                generator.ATTR_AWS_INSTANCE_IPV4: '10.0.5.92',
                generator.ATTR_EC2_INSTANCE_ID: 'i-1234',
                generator.ATTR_AWS_INSTANCE_PORT: '9080',
                generator.ATTR_AWS_INIT_HEALTH_STATUS: 'UNHEALTHY',
                generator.ATTR_AVAILABILITY_ZONE: 'az-xyz',
                generator.ATTR_REGION: 'eu-west-2',
                generator.ATTR_ECS_CLUSTER_NAME: 'my-cluster',
                generator.ATTR_ECS_SERVICE_NAME: 'svc-abc',
                generator.ATTR_ECS_TASK_DEFINITION_FAMILY: 'my-family',
            }
        })
        with msd:
            service_color = generator.DiscoveryServiceColor.from_single_id('1234')

            # Check loaded values
            self.assertEqual(service_color.namespace_id, 'xyz')
            self.assertEqual(service_color.service_id, '1234')
            self.assertEqual(service_color.service_arn, 'arn:blah:1234')
            self.assertEqual(service_color.discovery_service_name, 'a1234')

            # Check default values
            self.assertEqual(service_color.uses_http2, False)
            self.assertEqual(service_color.path_weights, {})
            self.assertEqual(service_color.instances, [])
            self.assertEqual(service_color.group_service_name, None)
            self.assertEqual(service_color.group_color_name, None)

            service_color.load_instances(True)

            self.assertEqual(service_color.namespace_id, 'xyz')
            self.assertEqual(service_color.service_id, '1234')
            self.assertEqual(service_color.service_arn, 'arn:blah:1234')
            self.assertEqual(service_color.discovery_service_name, 'a1234')
            self.assertEqual(service_color.uses_http2, False)
            self.assertEqual(service_color.group_service_name, 'service-A1')
            self.assertEqual(service_color.group_color_name, 'puce')
            self.assertEqual(service_color.path_weights, {
                '/path1': 10,
                '?/path2': 6,
                '/path3/path4': 8,
                '/path3/path5': 7,
                '/bad/weight': 1,
            })
            self.assertEqual(len(service_color.instances), 1)
            instance = service_color.instances[0]
            self.assertEqual(instance.instance_id, '1234-5678')
            self.assertEqual(instance.port_str, '9080')
            self.assertEqual(instance.ipv4, '10.0.5.92')
            self.assertEqual(instance.ec2_instance_id, 'i-1234')

    def test_read_service_id_not_exist(self) -> None:
        """
        The service never exists during the setup process.  This can happen in
        practice if the SERVICE_MEMBER references a non-existent service.
        """
        msd = MockServiceDiscovery()
        msd.mk_service_not_found('1234')
        with msd:
            service_color = generator.DiscoveryServiceColor.from_single_id('1234')
            self.assertIsNone(service_color)

    def test_read_service_disappears_before_load(self) -> None:
        """
        Check to make sure things work as expected when the service exists when first loaded,
        but then is removed before the instances are loaded.
        """
        msd = MockServiceDiscovery()
        msd.mk_service(service_id='1234a', name='a1234b', namespace_id='xyzc')
        msd.mk_instances_service_not_found(service_id='1234a')
        with msd:
            service_color = generator.DiscoveryServiceColor.from_single_id('1234a')
            self.assertIsNotNone(service_color)
            service_color.load_instances(True)
            self.assertEqual(service_color.namespace_id, 'xyzc')
            self.assertEqual(service_color.service_id, '1234a')
            self.assertEqual(service_color.service_arn, 'arn:blah:1234a')
            self.assertEqual(service_color.discovery_service_name, 'a1234b')
            self.assertEqual(service_color.uses_http2, False)
            self.assertIsNone(service_color.group_service_name)
            self.assertIsNone(service_color.group_color_name)
            self.assertEqual(service_color.path_weights, {})
            self.assertEqual(len(service_color.instances), 0)


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

    def mk_namespace_not_found(self, namespace_id: str) -> None:
        self.stubber.add_client_error(
            'get_namespace',
            expected_params={'Id': namespace_id},
            service_error_code='NamespaceNotFound'
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

    def mk_instances_service_not_found(self, service_id: str) -> None:
        self.stubber.add_client_error(
            'list_instances',
            expected_params={'ServiceId': service_id},
            service_error_code='ServiceNotFound'
        )

    def mk_instances(self, service_id: str, instance_attributes: Dict[str, Dict[str, str]]) -> None:
        self.stubber.add_response('list_instances', {
            'Instances': [
                {
                    'Id': iid,
                    'Attributes': dict(iat),
                } for iid, iat in instance_attributes.items()
            ],
        }, {'ServiceId': service_id})
