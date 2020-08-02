
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
            task_tags={'NJ_NAMESPACE': 'n1'},
            task_env={'NJ_PROTOCOL': 'HTTP2'},
            taskdef_tags={'NJ_SERVICE': 's1'},
            taskdef_env={'NJ_COLOR': 'c1', 'NJ_NAMESPACE': 'n2'},
        )
        task_empty = ecs.EcsTask(
            task_name='t2', task_arn='a2', taskdef_arn='ta', container_instance_arn='',
            host_ipv4='', container_host_ports={},
            task_tags={}, task_env={}, taskdef_tags={}, taskdef_env={},
        )
        self.assertEqual('n1', task_full.get_namespace_tag())
        self.assertIsNone(task_empty.get_namespace_tag())

        self.assertEqual('HTTP2', task_full.get_protocol_tag())
        self.assertEqual(None, task_empty.get_protocol_tag())

        self.assertEqual('s1', task_full.get_service_tag())
        self.assertEqual(None, task_empty.get_service_tag())

        self.assertEqual('c1', task_full.get_color_tag())
        self.assertEqual(None, task_empty.get_color_tag())

        self.assertEqual(('0', 1), task_full.get_route_container_host_port_for(1))
        self.assertEqual(('0', 1), task_empty.get_route_container_host_port_for(1))

    def test_route_use_case(self) -> None:  # pylint: disable=R0914
        """Test the standard usage of the route tags API."""
        task = ecs.EcsTask(
            task_name='t1', task_arn='a1', taskdef_arn='ta', container_instance_arn='',
            host_ipv4='', container_host_ports={'8080': 2021, 's1:8080': 2021},
            task_tags={
                # And for coverage, an invalid protocol...
                'NJ_PROTOCOL': 'tcp',

                'NJ_ROUTE_1': '/path/1',

                'NJ_ROUTE_3': '!/path/3',

                'NJ_ROUTE_16': '/other/16',
                'NJ_ROUTE_WEIGHT_16': '100',

                'NJ_ROUTE_22': '/that/22/path',
                'NJ_ROUTE_WEIGHT_22': 'xyz',
                'NJ_ROUTE_PORT_22': 's1:8080',

                'NJ_ROUTE_23': '{"some": true}',

                'NJ_ROUTE_XYZ': 'invalid',
            }, task_env={}, taskdef_tags={}, taskdef_env={},
        )

        # Coverage based checks...
        self.assertEqual('tcp', task.get_protocol_tag())

        routes = task.get_routes()
        self.assertEqual(5, len(routes))

        def get_route_index(index: int) -> ecs.RouteInfo:
            for route in routes:
                if route.index == index:
                    return route
            raise Exception('No such route: ' + str(index))  # pragma no cover

        route1 = get_route_index(1)
        self.assertEqual('/path/1', route1.data)
        self.assertEqual(1, route1.weight)
        self.assertTrue(route1.is_public_path)
        self.assertFalse(route1.is_private_path)
        self.assertFalse(route1.is_route_data)
        self.assertEqual('8080', route1.container_port)
        self.assertEqual(2021, route1.host_port)

        route3 = get_route_index(3)
        self.assertEqual('/path/3', route3.data)
        self.assertEqual(1, route3.weight)
        self.assertFalse(route3.is_public_path)
        self.assertTrue(route3.is_private_path)
        self.assertFalse(route3.is_route_data)
        self.assertEqual('8080', route3.container_port)
        self.assertEqual(2021, route3.host_port)

        route16 = get_route_index(16)
        self.assertEqual('/other/16', route16.data)
        self.assertEqual(100, route16.weight)
        self.assertTrue(route16.is_public_path)
        self.assertFalse(route16.is_private_path)
        self.assertFalse(route16.is_route_data)
        self.assertEqual('8080', route16.container_port)
        self.assertEqual(2021, route16.host_port)

        route22 = get_route_index(22)
        self.assertEqual('/that/22/path', route22.data)
        self.assertEqual(1, route22.weight)
        self.assertTrue(route22.is_public_path)
        self.assertFalse(route22.is_private_path)
        self.assertFalse(route22.is_route_data)
        self.assertEqual('s1:8080', route22.container_port)
        self.assertEqual(2021, route22.host_port)

        route23 = get_route_index(23)
        self.assertEqual({"some": True}, route23.data)
        self.assertFalse(route23.is_public_path)
        self.assertFalse(route23.is_private_path)
        self.assertTrue(route23.is_route_data)


class EcsTest(unittest.TestCase):
    """Test the ECS functions"""

    def setUp(self) -> None:
        self._orig_config = ecs.CONFIG

    def tearDown(self) -> None:
        ecs.CONFIG.clear()
        ecs.CONFIG.update(self._orig_config)

    def test_load_mesh_tasks__empty(self) -> None:
        """Test load_tasks_for_namespace with a basic setup."""
        mecs = MockEcs()
        with mecs:
            tasks = ecs.load_mesh_tasks([], None, None)
            self.assertEqual([], tasks)

    def test_load_mesh_tasks__basic(self) -> None:
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
                _mk_task({
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
                    'containers': [_mk_container({
                        'containerArn': 'aws:ecs:c1_container',
                        'taskArn': 'aws:ecs:c1_task1',
                        'name': 'c1_task1',

                        # This one uses an ec2 instance.
                        'networkBindings': [_mk_network_binding({
                            'containerPort': 9080,
                            'hostPort': 32769,
                        })],
                    })],
                }),

                # This one is ignored because of the tags...
                _mk_task({
                    'taskArn': 'aws:ecs:c1_task2',
                    'taskDefinitionArn': 'aws:ecs:c1_taskdef2',
                    'containerInstanceArn': 'aws:ecs:c1_instance',
                    'clusterArn': 'aws:ecs:cluster1',
                    'tags': [{'key': 'ROUTE_1', 'value': '/my/path'}],
                    'containers': [_mk_container({
                        'containerArn': 'aws:ecs:c1_task2_container',
                        'taskArn': 'aws:ecs:c1_task2',
                        'name': 'service_2',
                        'networkBindings': [
                            _mk_network_binding({'containerPort': 80, 'hostPort': 90}),
                            _mk_network_binding({
                                'bindIP': '127.0.0.1', 'containerPort': 82,
                                'hostPort': 92,
                            }),
                        ],
                    })],
                }),

                # As is this one...
                _mk_task({
                    'taskArn': 'aws:ecs:c1_task3',
                    'taskDefinitionArn': 'aws:ecs:c1_taskdef3',
                    'containerInstanceArn': 'aws:ecs:c1_instance',
                    'clusterArn': 'aws:ecs:cluster1',
                    'tags': [
                        {'key': 'NJ_NAMESPACE', 'value': 'namespace1'},
                        {'key': 'tag-r1', 'value': 'v2'},
                    ],
                    'containers': [_mk_container({
                        'containerArn': 'aws:ecs:c1_task2_container',
                        'taskArn': 'aws:ecs:c1_task3',
                        'name': 'service_4',
                        'networkBindings': [_mk_network_binding({
                            'bindIP': '10.0.0.1', 'containerPort': 80, 'hostPort': 90,
                        })],
                    })],
                }),

                # As is this one...
                _mk_task({
                    'taskArn': 'aws:ecs:c1_task4',
                    'taskDefinitionArn': 'aws:ecs:c1_taskdef3',
                    'containerInstanceArn': 'aws:ecs:c1_instance',
                    'clusterArn': 'aws:ecs:cluster1',
                    'tags': [{'key': 'tag-r1', 'value': 'v1'}],
                    'containers': [_mk_container({
                        'containerArn': 'aws:ecs:c1_task2_container',
                        'taskArn': 'aws:ecs:c1_task4',
                        'name': 'service_5',
                        'networkBindings': [_mk_network_binding({
                            'containerPort': 80, 'hostPort': 90,
                        })],
                        'networkInterfaces': [{
                            'attachmentId': 'attachment1234',
                            'privateIpv4Address': '10.9.8.7',
                            'ipv6Address': 'ipv6',
                        }],
                    })],
                }),
            ],
        )

        # Then, for each task that has undefined networks, load the container instances.
        mecs.mk_describe_container_instances(
            'cluster1', ('aws:ecs:c1_instance',),
            [_mk_container_instance({
                'containerInstanceArn': 'aws:ecs:c1_instance',
                'ec2InstanceId': 'i12345678',
                'tags': [],
                'attributes': [
                    {'name': 'ecs.subnet-id', 'value': 'subnet-1234'},
                    {'name': 'ecs.vpc-id', 'value': 'vpc-abcd'},
                ],
            })],
        )

        # And get the EC2 instance on which it runs.
        mecs.mk_describe_instances(['i12345678'], [_mk_ec2_instance({
            'InstanceId': 'i12345678',
            'PrivateDnsName': 'my.host.internal',
            'PrivateIpAddress': '1.2.3.4',
            'SubnetId': 'subnet-1234',
            'VpcId': 'vpc-abcd',
            'NetworkInterfaces': [_mk_network_interface({
                'PrivateIpAddress': '1.2.3.4',
                'PrivateIpAddresses': [_mk_ipv4_address({
                    'PrivateIpAddress': '1.2.3.4',
                })],
                'SubnetId': 'subnet-1234',
                'VpcId': 'vpc-abcd',
            })],
            'Tags': [],
        })])

        # Then get the resource tags for the taskdefs.
        mecs.mk_describe_task_definition('aws:ecs:c1_taskdef1', {
            'NJ_ROUTE_11': '/my/path',
            'NJ_NAMESPACE': 'namespace1',
            'NJ_PROXY_MODE': 'SERVICE',
            'NJ_SERVICE': 's1',
            'NJ_COLOR': 'c1',
        }, {})
        mecs.mk_describe_task_definition('aws:ecs:c1_taskdef2', {}, {'x': {
            'NJ_NAMESPACE': 'namespace1',
            'NJ_PROXY_MODE': 'GATEWAY',
        }})
        mecs.mk_describe_task_definition('aws:ecs:c1_taskdef3', {}, {})

        # Do the same thing with the second cluster.  This one contains only Fargate instances.
        mecs.mk_list_tasks('cluster2', ('aws:ecs:c2_task1',))
        mecs.mk_describe_tasks('cluster2', ('aws:ecs:c2_task1',), True, [_mk_task({
            'tags': [],
            'taskArn': 'aws:ecs:c2_task1',
            'taskDefinitionArn': 'aws:ecs:taskdef_3',
            'clusterArn': 'aws:ecs:cluster2',
            'containerInstanceArn': 'aws:ecs:fargate-1',
            'launchType': 'FARGATE',
            'containers': [
                _mk_container({
                    'containerArn': 'aws:ecs:c2_container1',
                    'taskArn': 'aws:ecs:c2_task1',
                    'name': 'service_1',
                    'networkBindings': [
                        _mk_network_binding({
                            'bindIP': '10.1.2.3',
                            'containerPort': 80,
                            'hostPort': 90,
                        }),
                        _mk_network_binding({
                            'bindIP': '0.0.0.0',
                            'containerPort': 81,
                            'hostPort': 91,
                            'protocol': 'udp',
                        }),
                        _mk_network_binding({
                            'bindIP': '0.0.0.0',
                            'containerPort': 82,
                            'hostPort': 92,
                        }),
                    ],
                    'networkInterfaces': [{
                        'attachmentId': 'attachment2',
                        'privateIpv4Address': '10.1.2.3',
                        'ipv6Address': ':::2',
                    }],
                }),
                _mk_container({
                    'containerArn': 'aws:ecs:c2_container2',
                    'taskArn': 'aws:ecs:c2_task1',
                    'name': 'service_2',
                    'networkBindings': [
                        _mk_network_binding({
                            'bindIP': '10.1.2.4',
                            'containerPort': 83,
                            'hostPort': 93,
                        }),
                    ],
                    'networkInterfaces': [{
                        'attachmentId': 'attachment1',
                        'privateIpv4Address': '10.1.2.4',
                        'ipv6Address': ':::3',
                    }],
                }),
            ],
            'overrides': {
                'containerOverrides': [{
                    'environment': [
                        {'name': 'NJ_PROXY_MODE', 'value': 'SERVICE'},
                        {'name': 'NJ_SERVICE', 'value': 'service_1'},
                        {'name': 'NJ_COLOR', 'value': 'color_1'},
                    ],
                }],
            },
        })])

        # Then, because all the host IPs are known, it skips directly to finding the taskdef tags.
        mecs.mk_describe_task_definition('aws:ecs:taskdef_3', {
            'tag-r1': 'v1',
            'NJ_ROUTE_6': '!/a/b/c',
            'NJ_WEIGHT_6': '12',
            'NJ_NAMESPACE': 'namespace1',
        }, {})

        with mecs:
            tasks = ecs.load_mesh_tasks(
                ['cluster1', 'cluster2'], 'tag-r1', 'v1',
            )
            self.assertEqual(
                [
                    "EcsTask(task_name='c1_task1', task_arn='aws:ecs:c1_task1', "
                    "taskdef_arn='aws:ecs:c1_taskdef1', "
                    "container_instance_arn='aws:ecs:c1_instance', host_ipv4='1.2.3.4', "
                    "container_host_ports=[('9080', 32769), ('c1_task1:9080', 32769)], "
                    "tags=[('NJ_COLOR', 'c1'), ('NJ_NAMESPACE', 'namespace1'), ('NJ_PROXY_MODE', "
                    "'SERVICE'), ('NJ_ROUTE_11', '/my/path'), ('NJ_SERVICE', 's1'), ('env_1', "
                    "'env_1_val'), ('tag-r1', 'v1')])",

                    "EcsTask(task_name='service_1', task_arn='aws:ecs:c2_task1', "
                    "taskdef_arn='aws:ecs:taskdef_3', container_instance_arn='aws:ecs:fargate-1', "
                    "host_ipv4='10.1.2.4', container_host_ports=[('80', 90), ('82', 92), ('83', "
                    "93), ('service_1:80', 90), ('service_1:82', 92), ('service_2:83', 93)], "
                    "tags=[('NJ_COLOR', 'color_1'), ('NJ_NAMESPACE', 'namespace1'), "
                    "('NJ_PROXY_MODE', 'SERVICE'), ('NJ_ROUTE_6', '!/a/b/c'), ('NJ_SERVICE', "
                    "'service_1'), ('NJ_WEIGHT_6', '12'), ('tag-r1', 'v1')])",
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
        filtered = ecs.filter_tasks(tasks, None, None)
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


def _mk_task(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'taskArn': 'aws:ecs:task',
        'taskDefinitionArn': 'aws:ecs:taskdef',
        'containerInstanceArn': 'aws:ecs:instance',
        'clusterArn': 'aws:ecs:cluster1',
        'tags': [],
        'overrides': {},
        'containers': [],
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
    }
    ret.update(overrides)
    return ret


def _mk_container(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'containerArn': 'aws:ecs:container',
        'taskArn': 'aws:ecs:task',
        'name': 'container',
        'image': 'image-name',
        'imageDigest': '1234',
        'runtimeId': 'blah',
        'lastStatus': 'RUNNING',  # What is the right value here?
        'networkBindings': [],
        'networkInterfaces': [],
        'healthStatus': 'HEALTHY',
        'cpu': '1.5',
        'memory': '32',
        'memoryReservation': '32',
        'gpuIds': [],
    }
    ret.update(overrides)
    return ret


def _mk_network_binding(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'bindIP': '0.0.0.0',
        'containerPort': 9080,
        'hostPort': 32769,
        'protocol': 'tcp',
    }
    ret.update(overrides)
    return ret


def _mk_container_instance(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'containerInstanceArn': 'aws:ecs:instance',
        'ec2InstanceId': 'i1234',
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
        'attributes': [],
        'registeredAt': datetime.datetime(2015, 1, 1),
        'attachments': [],
        'tags': [],
    }
    ret.update(overrides)
    return ret


def _mk_ec2_instance(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'InstanceId': 'i1234',
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
        'NetworkInterfaces': [],
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
    }
    ret.update(overrides)
    return ret


def _mk_network_interface(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
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
        'Ipv6Addresses': [],
        'MacAddress': 'string',
        'NetworkInterfaceId': 'string',
        'OwnerId': 'string',
        'PrivateDnsName': 'string',
        'PrivateIpAddress': '1.2.3.4',
        'PrivateIpAddresses': [],
        'SourceDestCheck': True,
        'Status': 'in-use',
        'SubnetId': 'subnet-1234',
        'VpcId': 'vpc-abcd',
        'InterfaceType': 'string',
    }
    ret.update(overrides)
    return ret


def _mk_ipv4_address(overrides: Dict[str, Any]) -> Dict[str, Any]:
    ret: Dict[str, Any] = {
        'Association': {
            'IpOwnerId': 'string',
            'PublicDnsName': 'string',
            'PublicIp': 'string',
        },
        'Primary': True,
        'PrivateDnsName': 'string',
        'PrivateIpAddress': '1.2.3.4',
    }
    ret.update(overrides)
    return ret
