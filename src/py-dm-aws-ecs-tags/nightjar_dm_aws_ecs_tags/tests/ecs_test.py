
"""Tests for the ecs module."""

from typing import List, Sequence, Dict, Optional, Any
import unittest
import datetime
import boto3
import botocore.stub  # type: ignore
import botocore.exceptions  # type: ignore
from .. import ecs


class EcsTaskTest(unittest.TestCase):
    """Test EcsTask class"""

    def test_tag_getters(self) -> None:
        """Test the tag getter methods"""
        task_full = ecs.EcsTask(
            task_name='t1', task_arn='a1', taskdef_arn='ta', container_instance_arn='',
            host_ipv4='', container_host_ports={},

            # tag/env order priority: task tag, taskdef tag, task env, taskdef env
            task_tags={'NAMESPACE': 'n1'},
            task_env={'PROTOCOL': 'HTTP2'},
            taskdef_tags={'SERVICE_NAME': 's1'},
            taskdef_env={'COLOR': 'c1', 'NAMESPACE': 'n2'},
        )
        task_empty = ecs.EcsTask(
            task_name='t2', task_arn='a2', taskdef_arn='ta', container_instance_arn='',
            host_ipv4='', container_host_ports={},
            task_tags={}, task_env={}, taskdef_tags={}, taskdef_env={},
        )
        self.assertEqual('n1', task_full.get_namespace_tag())
        self.assertIsNone(task_empty.get_namespace_tag())

        self.assertEqual('HTTP2', task_full.get_protocol())
        self.assertEqual('HTTP1.1', task_empty.get_protocol())

        self.assertEqual('s1', task_full.get_service_name())
        self.assertEqual('t2', task_empty.get_service_name())

        self.assertEqual('s1', task_full.get_service_name_tag())
        self.assertIsNone(task_empty.get_service_name_tag())

        self.assertEqual('c1', task_full.get_color())
        self.assertEqual('default', task_empty.get_color())

        self.assertEqual('a1', task_full.get_service_id())
        self.assertEqual('a2', task_empty.get_service_id())

        self.assertEqual(('0', 1), task_full.get_route_container_host_port_for(1))
        self.assertEqual(('0', 1), task_empty.get_route_container_host_port_for(1))

    def test_route_use_case(self) -> None:  # pylint: disable=R0914
        """Test the standard usage of the route tags API."""
        task = ecs.EcsTask(
            task_name='t1', task_arn='a1', taskdef_arn='ta', container_instance_arn='',
            host_ipv4='', container_host_ports={'8080': 2021, 's1:8080': 2021},
            task_tags={
                # And for coverage, an invalid protocol...
                'PROTOCOL': 'tcp',

                'ROUTE_1': '/path/1',

                'ROUTE_3': '!/path/3',

                'ROUTE_16': '/other/16',
                'WEIGHT_16': '100',

                'ROUTE_22': '/that/22/path',
                'WEIGHT_22': 'xyz',
                'PORT_22': 's1:8080',

                'ROUTE_XYZ': 'invalid',
            }, task_env={}, taskdef_tags={}, taskdef_env={},
        )

        # Coverage based checks...
        self.assertEqual('HTTP1.1', task.get_protocol())
        self.assertEqual(
            (None, 0, 'private'),
            task.get_route_weight_protection_for(0),
        )

        indicies = task.get_route_indicies()
        self.assertEqual(
            [1, 3, 16, 22],
            sorted(list(indicies)),
        )
        route1, weight1, protection1 = task.get_route_weight_protection_for(1)
        container_port1, host_port1 = task.get_route_container_host_port_for(1)
        self.assertEqual('/path/1', route1)
        self.assertEqual(1, weight1)
        self.assertEqual('public', protection1)
        self.assertEqual('8080', container_port1)
        self.assertEqual(2021, host_port1)

        route3, weight3, protection3 = task.get_route_weight_protection_for(3)
        container_port3, host_port3 = task.get_route_container_host_port_for(16)
        self.assertEqual('/path/3', route3)
        self.assertEqual(1, weight3)
        self.assertEqual('private', protection3)
        self.assertEqual('8080', container_port3)
        self.assertEqual(2021, host_port3)

        route16, weight16, protection16 = task.get_route_weight_protection_for(16)
        container_port16, host_port16 = task.get_route_container_host_port_for(16)
        self.assertEqual('/other/16', route16)
        self.assertEqual(100, weight16)
        self.assertEqual('public', protection16)
        self.assertEqual('8080', container_port16)
        self.assertEqual(2021, host_port16)

        route22, weight22, protection22 = task.get_route_weight_protection_for(22)
        container_port22, host_port22 = task.get_route_container_host_port_for(22)
        self.assertEqual('/that/22/path', route22)
        self.assertEqual(1, weight22)
        self.assertEqual('public', protection22)
        self.assertEqual('s1:8080', container_port22)
        self.assertEqual(2021, host_port22)


class EcsTest(unittest.TestCase):
    """Test the ECS functions"""

    def setUp(self) -> None:
        self._orig_config = ecs.CONFIG

    def tearDown(self) -> None:
        ecs.CONFIG.clear()
        ecs.CONFIG.update(self._orig_config)

    def test_load_tasks_for_namespace__empty(self) -> None:
        """Test load_tasks_for_namespace with a basic setup."""
        mecs = MockEcs()
        with mecs:
            tasks = ecs.load_tasks_for_namespace('n1', [], None, None)
            self.assertEqual([], tasks)

    def test_load_tasks_for_namespace__basic(self) -> None:
        """Test load_tasks_for_namespace with a basic setup."""
        mecs = MockEcs()

        # For the first cluster, grab the list of tasks.  We'll emulate paging.
        mecs.mk_list_tasks('cluster1', ('aws:ecs:c1_task1', 'aws:ecs:c1_task2'), 'xyz')
        mecs.mk_list_tasks('cluster1', ('aws:ecs:c1_task3', 'aws:ecs:c1_task4'), None, 'xyz')

        # Then, describe all the tasks.
        mecs.mk_describe_tasks(
            'cluster1',
            (
                'aws:ecs:c1_task1', 'aws:ecs:c1_task2', 'aws:ecs:c1_task3', 'aws:ecs:c1_task4',
            ),
            True,
            [
                {
                    'taskArn': 'aws:ecs:c1_task1',
                    'taskDefinitionArn': 'aws:ecs:c1_taskdef1',
                    'containerInstanceArn': 'aws:ecs:c1_instance',
                    'clusterArn': 'aws:ecs:cluster1',
                    'tags': [
                        {'key': 'tag-r1', 'value': 'v1'},
                    ],
                    'overrides': {
                        'containerOverrides': [{
                            'environment': [{'name': 'env_1', 'value': 'env_1_val'}],
                        }],
                    },
                    'containers': [{
                        'containerArn': 'aws:ecs:c1_container',
                        'taskArn': 'aws:ecs:c1_task1',
                        'name': 'c1_task1',
                        'image': 'image-name',
                        'imageDigest': '1234',
                        'runtimeId': 'blah',
                        'lastStatus': 'RUNNING',  # What is the right value here?

                        # This one uses an ec2 instance.
                        'networkBindings': [{
                            'bindIP': '0.0.0.0',
                            'containerPort': 9080,
                            'hostPort': 32769,
                            'protocol': 'tcp',
                        }],
                        'networkInterfaces': [],
                        'healthStatus': 'HEALTHY',
                        'cpu': '1.5',
                        'memory': '32',
                        'memoryReservation': '32',
                        'gpuIds': [],
                    }],
                    'attachments': [{}],
                    'attributes': [],
                    'availabilityZone': 'us-east-1a',
                    'capacityProviderName': 'blah',
                    'connectivity': 'CONNECTED',
                    'connectivityAt': datetime.datetime(2015, 1, 1),
                    'cpu': '1.5',
                    'createdAt': datetime.datetime(2015, 1, 1),
                    'desiredStatus': 'RUNNING',
                    'healthStatus': 'HEALTHY',
                    'inferenceAccelerators': [],
                    'lastStatus': 'RUNNING',
                    'launchType': 'EC2',
                    'memory': '32',
                    'platformVersion': '100',
                    'pullStartedAt': datetime.datetime(2015, 1, 1),
                    'pullStoppedAt': datetime.datetime(2015, 1, 1),
                    'startedAt': datetime.datetime(2015, 1, 1),
                    'startedBy': 'string',
                    'version': 123,
                },

                # This one is ignored because of the tags...
                {
                    'taskArn': 'aws:ecs:c1_task2',
                    'taskDefinitionArn': 'aws:ecs:c1_taskdef2',
                    'containerInstanceArn': 'aws:ecs:c1_instance',
                    'clusterArn': 'aws:ecs:cluster1',
                    'tags': [{'key': 'ROUTE_1', 'value': '/my/path'}],

                    'attachments': [],
                    'attributes': [],
                    'availabilityZone': 'us-east-1a',
                    'capacityProviderName': 'string',
                    'connectivity': 'CONNECTED',
                    'connectivityAt': datetime.datetime(2015, 1, 1),
                    'containers': [{
                        'containerArn': 'aws:ecs:c1_task2_container',
                        'taskArn': 'aws:ecs:c1_task2',
                        'name': 'service_2',
                        'image': 'string',
                        'imageDigest': 'string',
                        'runtimeId': 'string',
                        'lastStatus': 'string',
                        'exitCode': 123,
                        'reason': 'string',
                        'networkBindings': [
                            {
                                'bindIP': '0.0.0.0', 'containerPort': 80,
                                'hostPort': 90, 'protocol': 'tcp',
                            },
                            {
                                'bindIP': '127.0.0.1', 'containerPort': 82,
                                'hostPort': 92, 'protocol': 'tcp',
                            },
                        ],
                        'networkInterfaces': [],
                        'healthStatus': 'HEALTHY',
                        'cpu': 'string',
                        'memory': 'string',
                        'memoryReservation': 'string',
                        'gpuIds': [],
                    }],
                    'cpu': '10',
                    'createdAt': datetime.datetime(2015, 1, 1),
                    'desiredStatus': 'RUNNING',
                    'executionStoppedAt': datetime.datetime(2015, 1, 1),
                    'healthStatus': 'HEALTHY',
                    'inferenceAccelerators': [],
                    'lastStatus': 'RUNNING',
                    'launchType': 'EC2',
                    'overrides': {},
                    'memory': '32',
                    'platformVersion': '12',
                    'pullStartedAt': datetime.datetime(2015, 1, 1),
                    'pullStoppedAt': datetime.datetime(2015, 1, 1),
                    'startedAt': datetime.datetime(2015, 1, 1),
                    'startedBy': 'who',
                    'version': 123,
                },

                # As is this one...
                {
                    'taskArn': 'aws:ecs:c1_task3',
                    'taskDefinitionArn': 'aws:ecs:c1_taskdef3',
                    'containerInstanceArn': 'aws:ecs:c1_instance',
                    'clusterArn': 'aws:ecs:cluster1',
                    'tags': [
                        {'key': 'NAMESPACE', 'value': 'namespace1'},
                        {'key': 'tag-r1', 'value': 'v2'},
                    ],

                    'attachments': [],
                    'attributes': [],
                    'availabilityZone': 'us-east-1a',
                    'capacityProviderName': 'string',
                    'connectivity': 'CONNECTED',
                    'connectivityAt': datetime.datetime(2015, 1, 1),
                    'containers': [{
                        'containerArn': 'aws:ecs:c1_task2_container',
                        'taskArn': 'aws:ecs:c1_task3',
                        'name': 'service_4',
                        'image': 'string',
                        'imageDigest': 'string',
                        'runtimeId': 'string',
                        'lastStatus': 'string',
                        'exitCode': 123,
                        'reason': 'string',
                        'networkBindings': [{
                            'bindIP': '10.0.0.1', 'containerPort': 80,
                            'hostPort': 90, 'protocol': 'tcp',
                        }],
                        'networkInterfaces': [],
                        'healthStatus': 'HEALTHY',
                        'cpu': 'string',
                        'memory': 'string',
                        'memoryReservation': 'string',
                        'gpuIds': [],
                    }],
                    'cpu': '10',
                    'createdAt': datetime.datetime(2015, 1, 1),
                    'desiredStatus': 'RUNNING',
                    'executionStoppedAt': datetime.datetime(2015, 1, 1),
                    'healthStatus': 'HEALTHY',
                    'inferenceAccelerators': [],
                    'lastStatus': 'RUNNING',
                    'launchType': 'EC2',
                    'memory': '32',
                    'overrides': {},
                    'platformVersion': '12',
                    'pullStartedAt': datetime.datetime(2015, 1, 1),
                    'pullStoppedAt': datetime.datetime(2015, 1, 1),
                    'startedAt': datetime.datetime(2015, 1, 1),
                    'startedBy': 'who',
                    'version': 123,
                },

                # As is this one...
                {
                    'taskArn': 'aws:ecs:c1_task4',
                    'taskDefinitionArn': 'aws:ecs:c1_taskdef3',
                    'containerInstanceArn': 'aws:ecs:c1_instance',
                    'clusterArn': 'aws:ecs:cluster1',
                    'tags': [{'key': 'tag-r1', 'value': 'v1'}],

                    'attachments': [],
                    'attributes': [],
                    'availabilityZone': 'us-east-1a',
                    'capacityProviderName': 'string',
                    'connectivity': 'CONNECTED',
                    'connectivityAt': datetime.datetime(2015, 1, 1),
                    'containers': [{
                        'containerArn': 'aws:ecs:c1_task2_container',
                        'taskArn': 'aws:ecs:c1_task4',
                        'name': 'service_5',
                        'image': 'string',
                        'imageDigest': 'string',
                        'runtimeId': 'string',
                        'lastStatus': 'string',
                        'exitCode': 123,
                        'reason': 'string',
                        'networkBindings': [{
                            'bindIP': '0.0.0.0', 'containerPort': 80,
                            'hostPort': 90, 'protocol': 'tcp',
                        }],
                        'networkInterfaces': [{
                            'attachmentId': 'attachment1234',
                            'privateIpv4Address': '10.9.8.7',
                            'ipv6Address': 'ipv6',
                        }],
                        'healthStatus': 'HEALTHY',
                        'cpu': 'string',
                        'memory': 'string',
                        'memoryReservation': 'string',
                        'gpuIds': [],
                    }],
                    'cpu': '10',
                    'createdAt': datetime.datetime(2015, 1, 1),
                    'desiredStatus': 'RUNNING',
                    'executionStoppedAt': datetime.datetime(2015, 1, 1),
                    'healthStatus': 'HEALTHY',
                    'inferenceAccelerators': [],
                    'lastStatus': 'RUNNING',
                    'launchType': 'EC2',
                    'memory': '32',
                    'overrides': {},
                    'platformVersion': '12',
                    'pullStartedAt': datetime.datetime(2015, 1, 1),
                    'pullStoppedAt': datetime.datetime(2015, 1, 1),
                    'startedAt': datetime.datetime(2015, 1, 1),
                    'startedBy': 'who',
                    'version': 123,
                },
            ],
        )

        # Then, for each task that has undefined networks, load the container instances.
        mecs.mk_describe_container_instances(
            'cluster1', ('aws:ecs:c1_instance',),
            [{
                'containerInstanceArn': 'aws:ecs:c1_instance',
                'ec2InstanceId': 'i12345678',
                'capacityProviderName': 'x',
                'version': 123,
                'versionInfo': {},
                'remainingResources': [],
                'registeredResources': [],
                'status': 'ACTIVE',
                'statusReason': 'string',
                'agentConnected': True,
                'runningTasksCount': 2,
                'pendingTasksCount': 0,
                'agentUpdateStatus': 'UPDATED',
                'attributes': [
                    {
                        'name': 'ecs.subnet-id',
                        'value': 'subnet-1234',
                    },
                    {
                        'name': 'ecs.vpc-id',
                        'value': 'vpc-abcd',
                    },
                ],
                'registeredAt': datetime.datetime(2015, 1, 1),
                'attachments': [],
                'tags': [],
            }],
        )

        # And get the EC2 instance on which it runs.
        mecs.mk_describe_instances(['i12345678'], [{
            'InstanceId': 'i12345678',
            'AmiLaunchIndex': 123,
            'ImageId': 'abc',
            'InstanceType': 't1.micro',
            'KernelId': 'blah',
            'KeyName': 'blah',
            'LaunchTime': datetime.datetime(2015, 1, 1),
            'Monitoring': {'State': 'disabled'},
            'Placement': {},
            'Platform': 'Linux',
            'PrivateDnsName': 'my.host.internal',
            'PrivateIpAddress': '1.2.3.4',
            'ProductCodes': [],
            'RamdiskId': 'x',
            'State': {
                'Code': 123,
                'Name': 'running',
            },
            'StateTransitionReason': 'string',
            'SubnetId': 'subnet-1234',
            'VpcId': 'vpc-abcd',
            'Architecture': 'x86_64',
            'BlockDeviceMappings': [],
            'ClientToken': 'token',
            'EbsOptimized': False,
            'EnaSupport': False,
            'Hypervisor': 'xen',
            'IamInstanceProfile': {'Arn': 'x', 'Id': 'y'},
            'InstanceLifecycle': 'spot',
            'ElasticGpuAssociations': [],
            'ElasticInferenceAcceleratorAssociations': [],
            'NetworkInterfaces': [{
                'Association': {
                    'IpOwnerId': 'string',
                    'PublicDnsName': 'string',
                    'PublicIp': 'string',
                },
                'Attachment': {
                    'AttachTime': datetime.datetime(2015, 1, 1),
                    'AttachmentId': 'string',
                    'DeleteOnTermination': True,
                    'DeviceIndex': 123,
                    'Status': 'attached',
                },
                'Description': 'string',
                'Groups': [],
                'Ipv6Addresses': [{'Ipv6Address': 'string'}],
                'MacAddress': 'string',
                'NetworkInterfaceId': 'string',
                'OwnerId': 'string',
                'PrivateDnsName': 'string',
                'PrivateIpAddress': '1.2.3.4',
                'PrivateIpAddresses': [{
                    'Association': {
                        'IpOwnerId': 'string',
                        'PublicDnsName': 'string',
                        'PublicIp': 'string',
                    },
                    'Primary': True,
                    'PrivateDnsName': 'string',
                    'PrivateIpAddress': '1.2.3.4',
                }],
                'SourceDestCheck': True,
                'Status': 'in-use',
                'SubnetId': 'subnet-1234',
                'VpcId': 'vpc-abcd',
                'InterfaceType': 'string',
            }],
            'OutpostArn': 'string',
            'RootDeviceName': 'string',
            'RootDeviceType': 'instance-store',
            'SecurityGroups': [],
            'SourceDestCheck': True,
            'SpotInstanceRequestId': 'string',
            'SriovNetSupport': 'string',
            'StateReason': {'Code': 'string', 'Message': 'string'},
            'Tags': [],
            'VirtualizationType': 'hvm',
            'CpuOptions': {'CoreCount': 123, 'ThreadsPerCore': 123},
            'CapacityReservationId': 'string',
            'CapacityReservationSpecification': {},
            'HibernationOptions': {'Configured': False},
            'Licenses': [],
            'MetadataOptions': {},
        }])

        # Then get the resource tags for the taskdefs.
        mecs.mk_describe_task_definition('aws:ecs:c1_taskdef1', {
            'ROUTE_11': '/my/path',
            'NAMESPACE': 'namespace1',
        }, {})
        mecs.mk_describe_task_definition('aws:ecs:c1_taskdef2', {}, {'x': {
            'NAMESPACE': 'namespace1',
        }})
        mecs.mk_describe_task_definition('aws:ecs:c1_taskdef3', {}, {})

        # Do the same thing with the second cluster.  This one contains only Fargate instances.
        mecs.mk_list_tasks('cluster2', ('aws:ecs:c2_task1',))
        mecs.mk_describe_tasks('cluster2', ('aws:ecs:c2_task1',), True, [{
            'tags': [],
            'taskArn': 'aws:ecs:c2_task1',
            'taskDefinitionArn': 'aws:ecs:taskdef_3',
            'clusterArn': 'aws:ecs:cluster2',
            'containerInstanceArn': 'aws:ecs:fargate-1',
            'launchType': 'FARGATE',
            'containers': [
                {
                    'containerArn': 'aws:ecs:c2_container1',
                    'taskArn': 'aws:ecs:c2_task1',
                    'name': 'service_1',
                    'image': 'image1',
                    'imageDigest': 'imageDigest1',
                    'runtimeId': 'runtimeId1',
                    'lastStatus': 'lastStatus1',
                    'networkBindings': [
                        {
                            'bindIP': '10.1.2.3',
                            'containerPort': 80,
                            'hostPort': 90,
                            'protocol': 'tcp',
                        },
                        {
                            'bindIP': '0.0.0.0',
                            'containerPort': 81,
                            'hostPort': 91,
                            'protocol': 'udp',
                        },
                        {
                            'bindIP': '0.0.0.0',
                            'containerPort': 82,
                            'hostPort': 92,
                            'protocol': 'tcp',
                        },
                    ],
                    'networkInterfaces': [{
                        'attachmentId': 'attachmentId1',
                        'privateIpv4Address': '10.1.2.3',
                        'ipv6Address': 'ipv6Address1',
                    }],
                    'healthStatus': 'HEALTHY',
                    'cpu': 'cpu1',
                    'memory': 'memory1',
                    'memoryReservation': 'memoryReservation1',
                    'gpuIds': [],
                },
                {
                    'containerArn': 'aws:ecs:c2_container2',
                    'taskArn': 'aws:ecs:c2_task1',
                    'name': 'service_2',
                    'image': 'image2',
                    'imageDigest': 'imageDigest2',
                    'runtimeId': 'runtimeId2',
                    'lastStatus': 'lastStatus2',
                    'networkBindings': [
                        {
                            'bindIP': '10.1.2.4',
                            'containerPort': 83,
                            'hostPort': 93,
                            'protocol': 'tcp',
                        },
                    ],
                    'networkInterfaces': [{
                        'attachmentId': 'attachmentId2',
                        'privateIpv4Address': '10.1.2.4',
                        'ipv6Address': 'ipv6Address2',
                    }],
                    'healthStatus': 'HEALTHY',
                    'cpu': 'cpu2',
                    'memory': 'memory2',
                    'memoryReservation': 'memoryReservation3',
                    'gpuIds': [],
                },
            ],

            'attachments': [],
            'attributes': [],
            'availabilityZone': 'us-west-1b',
            'capacityProviderName': 'capacityProviderName1',
            'connectivity': 'CONNECTED',
            'connectivityAt': datetime.datetime(2015, 1, 1),
            'cpu': 'cpuA',
            'createdAt': datetime.datetime(2015, 1, 1),
            'desiredStatus': 'desiredStatusA',
            'executionStoppedAt': datetime.datetime(2015, 1, 1),
            'group': 'groupA',
            'healthStatus': 'HEALTHY',
            'inferenceAccelerators': [],
            'lastStatus': 'lastStatusA',
            'memory': 'memoryA',
            'overrides': {},
            'platformVersion': 'platformVersionA',
            'pullStartedAt': datetime.datetime(2015, 1, 1),
            'pullStoppedAt': datetime.datetime(2015, 1, 1),
            'startedAt': datetime.datetime(2015, 1, 1),
            'startedBy': 'startedByA',
            'version': 123,
        }])

        # Then, because all the host IPs are known, it skips directly to finding the taskdef tags.
        mecs.mk_describe_task_definition('aws:ecs:taskdef_3', {
            'tag-r1': 'v1',
            'ROUTE_6': '!/a/b/c',
            'WEIGHT_6': '12',
            'NAMESPACE': 'namespace1',
        }, {})

        with mecs:
            tasks = ecs.load_tasks_for_namespace(
                'namespace1', ['cluster1', 'cluster2'], 'tag-r1', 'v1',
            )
            self.assertEqual(
                [
                    "EcsTask(task_name='c1_task1', task_arn='aws:ecs:c1_task1', "
                    "taskdef_arn='aws:ecs:c1_taskdef1', "
                    "container_instance_arn='aws:ecs:c1_instance', host_ipv4='1.2.3.4', "
                    "container_host_ports=[('9080', 32769), ('c1_task1:9080', 32769)], "
                    "tags=[('NAMESPACE', 'namespace1'), ('ROUTE_11', '/my/path'), ('env_1', "
                    "'env_1_val'), ('tag-r1', 'v1')])",

                    "EcsTask(task_name='service_1', task_arn='aws:ecs:c2_task1', "
                    "taskdef_arn='aws:ecs:taskdef_3', container_instance_arn='aws:ecs:fargate-1', "
                    "host_ipv4='10.1.2.4', container_host_ports=[('80', 90), ('82', 92), ('83', "
                    "93), ('service_1:80', 90), ('service_1:82', 92), ('service_2:83', 93)], "
                    "tags=[('NAMESPACE', 'namespace1'), ('ROUTE_6', '!/a/b/c'), ('WEIGHT_6', "
                    "'12'), ('tag-r1', 'v1')])",
                ],
                [repr(task) for task in tasks],
            )

    def test_add_taskdef_tags(self) -> None:
        """Test add_taskdef_tags"""
        mecs = MockEcs()
        mecs.mk_describe_task_definition('ecs-taskdef-1', {'k1': 'v1'}, {})
        mecs.mk_describe_task_definition('ecs-taskdef-2', {'k2': 'v2'}, {'abc': {'k3': 'v3'}})
        tasks = [
            ecs.EcsTask(
                task_name='t1',
                task_arn='a1',
                taskdef_arn='ecs-taskdef-1',
                container_instance_arn='',
                host_ipv4='',
                container_host_ports={},
                task_tags={'k': 'v'}, task_env={}, taskdef_env={}, taskdef_tags={},
            ),
            ecs.EcsTask(
                task_name='t2',
                task_arn='a1',
                taskdef_arn='ecs-taskdef-1',
                container_instance_arn='',
                host_ipv4='',
                container_host_ports={},
                task_tags={'k1': 'other', 'k': 'v'}, task_env={}, taskdef_env={}, taskdef_tags={},
            ),
            ecs.EcsTask(
                task_name='t1',
                task_arn='a1',
                taskdef_arn='ecs-taskdef-2',
                container_instance_arn='',
                host_ipv4='',
                container_host_ports={},
                task_tags={}, task_env={}, taskdef_env={}, taskdef_tags={},
            ),
        ]
        with mecs:
            ecs.add_taskdef_tags(tasks)

        self.assertEqual(tasks[0].get_tags(), {'k': 'v', 'k1': 'v1'})
        self.assertEqual(tasks[1].get_tags(), {'k': 'v', 'k1': 'other'})
        self.assertEqual(tasks[2].get_tags(), {'k2': 'v2', 'k3': 'v3'})

    def test_load_taskdef_tags(self) -> None:
        """Test the load_taskdef_tags method"""
        mecs = MockEcs()
        mecs.mk_describe_task_definition(
            'aws:ecs:us-east-1:12347890/taskdef/x',
            {'a': 'b'},
            {'x': {'c': 'd'}, 'y': {'e': 'f'}},
        )
        with mecs:
            tags, env = ecs.load_taskdef_tags_env('aws:ecs:us-east-1:12347890/taskdef/x')
        self.assertEqual(
            {'a': 'b'},
            tags,
        )
        self.assertEqual(
            {'c': 'd', 'e': 'f'},
            env,
        )

    def test_set_aws_config(self) -> None:
        """Tests set_aws_config"""
        ecs.set_aws_config({'x': 'y'})
        self.assertEqual({'x': 'y'}, ecs.CONFIG)
        ecs.set_aws_config({'a': 'b'})
        self.assertEqual({'a': 'b'}, ecs.CONFIG)

    def test_dt_opt_get(self) -> None:
        """Test the dt_opt_get function."""
        self.assertIsNone(ecs.dt_opt_get([], 1))  # type: ignore
        self.assertIsNone(ecs.dt_opt_get({}, 'x'))
        self.assertIsNone(ecs.dt_opt_get([], 'x'))  # type: ignore

    def test_get_session__fails(self) -> None:
        """Test the get_session function."""
        ecs.CONFIG['AWS_REGION'] = 'us-west-2'
        ecs.CONFIG['AWS_PROFILE'] = 'my-aws-profile-does-not-exist'
        try:
            ecs.get_session()
            # self.assertIsNotNone(session)
            # self.assertEqual('my-aws-profile-does-not-exist', session.profile_name)
            # self.assertEqual('us-west-2', session.region_name)
            self.fail(
                'Should have raised an error due to profile could not be found.'
            )  # pragma no cover
        except botocore.exceptions.ProfileNotFound:
            pass

    def test_filter_tasks_color_not_set(self) -> None:
        """Test filter_tasks if the color is not set."""
        tasks = [ecs.EcsTask(
            task_name='tn1', task_arn='ta1', taskdef_arn='tda1',
            container_instance_arn='cia1', host_ipv4='1.2.3.4',
            container_host_ports={}, task_tags={}, taskdef_tags={}, task_env={},
            taskdef_env={'namespace': 'n1'},
        )]
        filtered = ecs.filter_tasks(tasks, 'n1', None, None)
        self.assertEqual([], filtered)


class MockEcs:
    """Mock AWS ECS wrapper."""
    __slots__ = (
        'ecs_client', '_ecs_client', 'ecs_stubber', 'old_ecs_client',
        'ec2_client', '_ec2_client', 'ec2_stubber', 'old_ec2_client',
    )

    def __init__(self) -> None:
        self.ecs_client: Any = None
        self._ecs_client = boto3.client('ecs', region_name='us-west-1')
        self.ecs_stubber = botocore.stub.Stubber(self._ecs_client)
        self.old_ecs_client: Any = None

        self.ec2_client: Any = None
        self._ec2_client = boto3.client('ec2', region_name='us-west-1')
        self.ec2_stubber = botocore.stub.Stubber(self._ec2_client)
        self.old_ec2_client: Any = None

    def __enter__(self) -> None:
        self.ecs_client = self._ecs_client
        self.old_ecs_client = ecs.CLIENTS.get('ecs')
        ecs.CLIENTS['ecs'] = self._ecs_client
        self.ecs_stubber.__enter__()

        self.ec2_client = self._ec2_client
        self.old_ec2_client = ecs.CLIENTS.get('ec2')
        ecs.CLIENTS['ec2'] = self._ec2_client
        self.ec2_stubber.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self.ec2_client = None
        if self.old_ec2_client is None:
            del ecs.CLIENTS['ec2']
        else:
            ecs.CLIENTS['ec2'] = self.old_ec2_client  # pragma no cover
            self.old_ec2_client = None  # pragma no cover
        self.ec2_stubber.__exit__(exc_type, exc_val, exc_tb)

        self.ecs_client = None
        if self.old_ecs_client is None:
            del ecs.CLIENTS['ecs']
        else:
            ecs.CLIENTS['ecs'] = self.old_ecs_client  # pragma no cover
            self.old_ecs_client = None  # pragma no cover
        self.ecs_stubber.__exit__(exc_type, exc_val, exc_tb)

    # def mk_cluster_not_found(self, cluster_name: str) -> None:
    #     """Add a cluster-not-found response."""
    #     self.ecs_stubber.add_client_error(
    #         'get_namespace',
    #         expected_params={'Id': cluster_name},
    #         service_error_code='ClusterNotFound',
    #     )

    def mk_describe_task_definition(
            self, taskdef_arn: str,
            tags: Dict[str, str], container_envs: Dict[str, Dict[str, str]],
    ) -> None:
        """Add a service-not-found response."""
        self.ecs_stubber.add_response('describe_task_definition', {
            'taskDefinition': {
                'taskDefinitionArn': taskdef_arn,
                'containerDefinitions': [
                    {
                        'name': container_name,
                        'image': container_name + '-image',
                        # 'repositoryCredentials': { ... },
                        'cpu': 123,
                        'memory': 123,
                        'memoryReservation': 123,
                        'links': [],
                        'portMappings': [],
                        'essential': True,
                        'entryPoint': [],
                        'command': [],
                        'environment': [
                            {
                                'name': key,
                                'value': val,
                            }
                            for key, val in container_env.items()
                        ],
                        'environmentFiles': [],
                        'mountPoints': [],
                        'volumesFrom': [],
                        # 'linuxParameters': { ... },
                        'secrets': [],
                        'dependsOn': [],
                        'startTimeout': 123,
                        'stopTimeout': 123,
                        'hostname': container_name,
                        'user': 'user',
                        'workingDirectory': '/',
                        'disableNetworking': False,
                        'privileged': False,
                        'readonlyRootFilesystem': False,
                        'dnsServers': [],
                        'dnsSearchDomains': [],
                        'extraHosts': [],
                        'dockerSecurityOptions': [],
                        'interactive': False,
                        'pseudoTerminal': False,
                        # 'dockerLabels': { ... },
                        'ulimits': [],
                        # 'logConfiguration': { ... },
                        # 'healthCheck': { ... },
                        'systemControls': [],
                        'resourceRequirements': [],
                        # 'firelensConfiguration': { ... },
                    }
                    for container_name, container_env in container_envs.items()
                ],
                'family': 'string',
                'taskRoleArn': 'string',
                'executionRoleArn': 'string',
                'networkMode': 'bridge',  # could force this to be aws or bridge.
                'revision': 123,
                'volumes': [],
                'status': 'ACTIVE',
                'requiresAttributes': [],
                'placementConstraints': [],
                'compatibilities': ['EC2', 'FARGATE'],
                'requiresCompatibilities': ['EC2', 'FARGATE'],
                'cpu': 'string',
                'memory': 'string',
                'inferenceAccelerators': [],
                'pidMode': 'host',
                'ipcMode': 'host',
                # 'proxyConfiguration': { ... },
            },

            'tags': [
                {'key': key, 'value': val}
                for key, val in tags.items()
            ],
        }, {'taskDefinition': taskdef_arn, 'include': ['TAGS']})

    def mk_list_tasks(
            self, cluster: str, task_arns: Sequence[str],
            next_token: Optional[str] = None, prev_token: Optional[str] = None,
    ) -> None:
        """Add response for list_tasks"""
        data: Dict[str, Any] = {
            'taskArns': list(task_arns),
        }
        request = {
            'cluster': cluster,
        }
        if next_token:
            data['nextToken'] = next_token
        if prev_token:
            request['nextToken'] = prev_token
        self.ecs_stubber.add_response('list_tasks', data, request)

    def mk_describe_tasks(
            self,
            cluster: str, task_arns: Sequence[str], include_tags: bool,
            task_descriptions: Sequence[Dict[str, Any]],
    ) -> None:
        """Add describe_tasks call."""
        data = {'tasks': list(task_descriptions)}
        request = {'cluster': cluster, 'tasks': list(task_arns)}
        if include_tags:
            request['include'] = ['TAGS']
        self.ecs_stubber.add_response('describe_tasks', data, request)

    def mk_describe_container_instances(
            self, cluster: str, container_instances: Sequence[str],
            instance_descriptions: Sequence[Dict[str, Any]],
    ) -> None:
        """Add describe_container_instances call"""
        data = {'containerInstances': list(instance_descriptions)}
        request = {'cluster': cluster, 'containerInstances': list(container_instances)}
        self.ecs_stubber.add_response('describe_container_instances', data, request)

    def mk_describe_instances(
            self, instance_ids: Sequence[str], instance_data: List[Dict[str, Any]],
    ) -> None:
        """Add ec2 describe_instances call"""
        data = {
            'Reservations': [{
                'Groups': [],
                'Instances': list(instance_data),
                'OwnerId': 'xyz',
                'RequesterId': 'abc',
                'ReservationId': '123',
            }],
        }
        request = {'InstanceIds': list(instance_ids)}
        self.ec2_stubber.add_response('describe_instances', data, request)
