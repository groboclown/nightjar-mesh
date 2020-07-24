
"""AWS ECS Interface."""

from typing import Dict, Tuple, List, Optional, Iterable, Set, Literal, Union, Any
import re
import boto3
# from botocore.exceptions import ClientError  # type: ignore
from botocore.config import Config  # type: ignore


RouteProtection = Literal['public', 'private']
PROTECTION_PUBLIC: RouteProtection = 'public'
PROTECTION_PRIVATE: RouteProtection = 'private'


PROTOCOL__HTTP1_1 = 'HTTP1.1'
PROTOCOL__HTTP2 = 'HTTP2'
SUPPORTED_PROTOCOLS = (
    PROTOCOL__HTTP1_1,
    PROTOCOL__HTTP2,
)

ROUTE_TAG_MATCHER = re.compile(r'^ROUTE_(\d+)$')


class EcsTask:
    """An ECS task with 1 or more containers.
    Should to look into adding IPv6 support.
    """
    __slots__ = (
        'task_name', 'task_arn', 'taskdef_arn', 'container_instance_arn',
        'host_ipv4', 'container_host_ports',
        'task_tags', 'taskdef_tags', 'task_env', 'taskdef_env',
    )

    def __init__(  # pylint: disable=R0913
            self,
            task_name: str,
            task_arn: str,
            taskdef_arn: str,
            container_instance_arn: Optional[str],
            host_ipv4: str,
            container_host_ports: Dict[str, int],
            task_tags: Dict[str, str],
            taskdef_tags: Dict[str, str],
            task_env: Dict[str, str],
            taskdef_env: Dict[str, str],
    ) -> None:
        self.task_name = task_name
        self.task_arn = task_arn
        self.taskdef_arn = taskdef_arn
        self.container_instance_arn = container_instance_arn
        self.host_ipv4 = host_ipv4
        self.container_host_ports = dict(container_host_ports)
        self.task_tags = dict(task_tags)
        self.taskdef_tags = dict(taskdef_tags)
        self.task_env = dict(task_env)
        self.taskdef_env = dict(taskdef_env)

    def __repr__(self) -> str:
        return (
            f'EcsTask('
            f'task_name={repr(self.task_name)}, '
            f'task_arn={repr(self.task_arn)}, '
            f'taskdef_arn={repr(self.taskdef_arn)}, '
            f'container_instance_arn={repr(self.container_instance_arn)}, '
            f'host_ipv4={repr(self.host_ipv4)}, '
            f'container_host_ports={repr(sorted(list(self.container_host_ports.items())))}, '
            f'tags={repr(sorted(list(self.get_tags().items())))})'
        )

    def get_tags(self) -> Dict[str, str]:
        """Fetch the current 'tags', which is a combination of tags and environment variables,
        pulled in a specific order.
        """
        ret: Dict[str, str] = dict(self.taskdef_env)
        ret.update(self.task_env)
        ret.update(self.taskdef_tags)
        ret.update(self.task_tags)
        return ret

    def get_tag_keys(self) -> Set[str]:
        """Get all the keys in the 'tags'."""
        ret = set(self.task_env.keys())
        ret.update(self.task_tags.keys())
        ret.update(self.taskdef_env.keys())
        ret.update(self.taskdef_tags.keys())
        return ret

    def get_tag_with(self, key: str, default_value: str) -> str:
        """Get a tag with a default value."""
        res = self.get_tag(key, default_value)
        assert res is not None
        return res

    def get_tag(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """Get the 'tag' using correct ordering.

        Search order:
            - task tag (these can change during runtime)
            - taskdef tags (these can change during runtime)
            - task override env.  Note that each container can have its own set of overrides.
                The order is non-determinant.
            - taskdef env
        """
        val = self.task_tags.get(key)
        if not val:
            val = self.taskdef_tags.get(key)
            if not val:
                val = self.task_env.get(key)
                if not val:
                    val = self.taskdef_env.get(key, default_value)
        return val

    def get_namespace(self) -> str:
        """The namespace, or default if not given."""
        return self.get_namespace_tag() or 'default'

    def get_namespace_tag(self) -> Optional[str]:
        """The optional namespace tag on the task."""
        return self.get_tag('NAMESPACE')

    def get_protocol(self) -> str:
        """The optional protocol defined for this service."""
        protocol = self.get_tag_with('PROTOCOL', PROTOCOL__HTTP1_1)
        if protocol.upper() in SUPPORTED_PROTOCOLS:
            return protocol.upper()
        return PROTOCOL__HTTP1_1

    def get_service_name(self) -> str:
        """The name of the service."""
        return self.get_service_name_tag() or self.task_name

    def get_service_name_tag(self) -> Optional[str]:
        """The service name tag, if given."""
        return self.get_tag('SERVICE_NAME')

    def get_color(self) -> str:
        """The color for this service."""
        return self.get_tag('COLOR') or 'default'

    def get_service_id(self) -> str:
        """The opaque ID for this service instance."""
        return self.task_arn

    def get_route_container_host_port_for(self, index: int) -> Tuple[str, int]:
        """Finds the (container) PORT value for the index, and grabs the
        mapped-to host port.  If no PORT is given, or the container port
        is not found, then the first host port is used.  If nothing valid
        is found, then this returns 1.

        The PORT* value can be `container-name:port`, to allow for
        differentiating between containers that share the same container port.

        Returns (container port, host port).  Container port is 0 if it is
            not a valid value.
        """
        container_port_str = self.get_tag('PORT_' + str(index))
        if not container_port_str:
            container_port_str = self.get_tag('PORT')
        if not container_port_str:
            # Return the first host port.  If it isn't an integer,
            # then the default value is returned.
            for container_port_str, host_port in self.container_host_ports.items():
                return container_port_str, host_port
            # No port known.  Return a value that isn't valid, but won't cause an error.
            return '0', 1
        host_port = self.container_host_ports.get(container_port_str, 1)
        return container_port_str, host_port

    def get_route_weight_protection_for(
            self, index: int,
    ) -> Tuple[Optional[str], int, RouteProtection]:
        """Get the route, weight, and protection for the route at the given index."""
        route = self.get_tag('ROUTE_' + str(index))
        if not route:
            return None, 0, PROTECTION_PRIVATE
        protection = PROTECTION_PUBLIC
        if route[0] == '!':
            route = route[1:]
            protection = PROTECTION_PRIVATE
        weight_str = self.get_tag('WEIGHT_' + str(index))
        if weight_str:
            try:
                weight = int(weight_str)
            except ValueError:
                weight = 1
        else:
            weight = 1
        return route, weight, protection

    def get_route_indicies(self) -> Iterable[int]:
        """Find all the route indicies in the tags."""
        ret: List[int] = []
        for tag_name in self.get_tag_keys():
            match = ROUTE_TAG_MATCHER.match(tag_name)
            if match:
                try:
                    index = int(match.group(1))
                    ret.append(index)
                except ValueError:  # pragma no cover
                    # Because of the regular expression, this shouldn't happen...
                    pass  # pragma no cover
        return ret


def load_tasks_for_namespace(
        namespace: str,
        cluster_names: Iterable[str],
        required_tag_name: Optional[str],
        required_tag_value: Optional[str],
) -> Iterable[EcsTask]:
    """
    Find tasks that match up to the requirements for this configuration.
    """
    ret: List[EcsTask] = []
    for cluster_name in cluster_names:
        ret.extend(filter_tasks(
            load_tasks_for_cluster(cluster_name),
            namespace,
            required_tag_name,
            required_tag_value,
        ))
    return ret


def filter_tasks(
        tasks: Iterable[EcsTask],
        namespace: str,
        required_tag_name: Optional[str],
        required_tag_value: Optional[str],
) -> Iterable[EcsTask]:
    """Filter out tasks that do not meet the requirements for being in the mesh."""
    ret: List[EcsTask] = []
    for task in tasks:
        if required_tag_name:
            value = task.get_tag(required_tag_name, None)
            if (
                    # the tag is not set (value is None)
                    value is None
                    or
                    # the tag is set to a value, a specific value is required, and the tag's
                    # value does not correspond to that required value.
                    (required_tag_value and value != required_tag_value)
            ):
                continue
            # Else, the tag is assigned to a value, and either
            # the value doesn't matter, or the value matches the required value.
        if task.get_namespace() == namespace and task.get_color() is not None:
            ret.append(task)
    return ret


def load_tasks_for_cluster(cluster_name: str) -> Iterable[EcsTask]:
    """
    Runs ListTasks on the cluster, then runs DescribeTasks to get the details.
    """
    tasks = load_tasks_by_arns(cluster_name, get_task_arns_in_cluster(cluster_name))
    populate_ec2_ip_for_tasks(cluster_name, tasks)
    add_taskdef_tags(tasks)
    return tasks


def get_task_arns_in_cluster(cluster_name: str) -> Iterable[str]:
    """Find the task arns running in the given cluster."""
    ret: List[str] = []
    paginator = get_ecs_client().get_paginator('list_tasks')
    response_iterator = paginator.paginate(cluster=cluster_name)
    for page in response_iterator:
        for task_arn in page['taskArns']:
            ret.append(task_arn)
    return ret


def load_tasks_by_arns(
        cluster_name: str, task_arns: Iterable[str]
) -> List[EcsTask]:
    """
    Reads the definition for these tasks.
    """
    # Can query up to 100 task arns per request.
    all_task_arns = list(set(task_arns))
    discovered_tasks: List[EcsTask] = []
    index = 0

    while index < len(all_task_arns):
        next_index = min(index + 100, len(all_task_arns))
        batch = sorted(all_task_arns[index:next_index])  # sort for testing purposes...
        index = next_index
        response = get_ecs_client().describe_tasks(
            cluster=cluster_name,
            tasks=batch,
            include=['TAGS'],  # extremely important!!!
        )
        # This gets a bit tricky.  Each task has 1 or more containers, which have their
        # own port mappings.  There is a possibility for overlap, but this shouldn't
        # matter, because of the PORT tag should reference a unique container port.
        container_host_ports: Dict[str, int] = {}
        container_env: Dict[str, str] = {}
        for task in response['tasks']:
            service_name = ''
            host_ipv4 = ''
            for container in task['containers']:
                service_name, host_ipv4 = process_task_container(
                    container, container_host_ports,
                    service_name, host_ipv4,
                )
            if 'overrides' in task and 'containerOverrides' in task['overrides']:
                for override in task['overrides']['containerOverrides']:
                    # NOTE: This does not check environmentFiles.
                    if 'environment' in override:
                        for env in override['environment']:
                            container_env[dt_str(env, 'name')] = dt_str(env, 'value')

            discovered_tasks.append(EcsTask(
                task_name=service_name,
                task_arn=dt_str(task, 'taskArn'),
                taskdef_arn=dt_str(task, 'taskDefinitionArn'),

                # the instance could be None if run in Fargate.
                container_instance_arn=dt_opt_str(task, 'containerInstanceArn'),

                host_ipv4=host_ipv4,
                container_host_ports=container_host_ports,
                task_tags={
                    dt_str(tag, 'key'): dt_str(tag, 'value')
                    for tag in task['tags']
                },
                task_env=container_env,

                taskdef_tags={},
                taskdef_env={},
            ))
    return discovered_tasks


def process_task_container(
        container: Dict[str, Any],
        container_host_ports: Dict[str, int],
        prev_service_name: Optional[str],
        prev_host_ipv4: str,
) -> Tuple[str, str]:
    """Perform processing of the task container result."""
    container_name = dt_str(container, 'name')
    service_name = prev_service_name or container_name
    host_ipv4 = prev_host_ipv4
    for binding in container.get('networkBindings', []):
        # Ignore all but 'tcp' protocols.
        if dt_str(binding, 'protocol') != 'tcp':
            continue
        binding_ip = dt_str(binding, 'bindIP')
        if binding_ip == '127.0.0.1':
            # Ignore localhost stuff.  This probably won't ever happen.
            continue
        if binding_ip != '0.0.0.0':
            # This is the IP address that the port is listening on.
            host_ipv4 = binding_ip
        # If there's an overlap with an existing registration, overwrite it.
        container_port = dt_int(binding, 'containerPort')
        host_port = dt_int(binding, 'hostPort')
        container_host_ports['{0}:{1}'.format(
            container_name, container_port
        )] = host_port
        container_host_ports[str(container_port)] = host_port
    if not host_ipv4:
        # See if there's an awsvpc network, which will be the case in fargate instances.
        for interface in container.get('networkInterfaces', []):
            interface_ip = dt_str(interface, 'privateIpv4Address')
            if interface_ip not in ('127.0.0.1', '0.0.0.0',):
                host_ipv4 = interface_ip
    return service_name, host_ipv4


def populate_ec2_ip_for_tasks(cluster_name: str, tasks: Iterable[EcsTask]) -> None:
    """Load the IP addresses into the tasks, for the IPs not yet populated."""

    container_instance_arns: Set[str] = set()
    for task in tasks:
        if task.container_instance_arn and not task.host_ipv4:
            container_instance_arns.add(task.container_instance_arn)

    if not container_instance_arns:
        # Early exit for nothing to do.
        return

    host_ipv4_by_container_instance_arn = load_ec2_host_ip_by_info(
        load_ec2_info_by_container_instances(
            cluster_name, container_instance_arns,
        )
    )

    for task in tasks:
        if (
                task.container_instance_arn
                and task.container_instance_arn in host_ipv4_by_container_instance_arn
        ):
            task.host_ipv4 = host_ipv4_by_container_instance_arn[task.container_instance_arn]


def load_ec2_info_by_container_instances(
        cluster_name: str, container_instances: Iterable[str]
) -> Dict[str, Tuple[str, str, str]]:
    """
    Finds the ec2 instance ID, vpc, and subnet by container instance ARN.
    """
    ret: Dict[str, Tuple[str, str, str]] = {}
    all_instance_arns = list(set(container_instances))
    # Can query up to 100 container instance arns per request.
    index = 0
    while index < len(all_instance_arns):
        next_index = min(index + 100, len(all_instance_arns))
        batch = all_instance_arns[index:next_index]
        index = next_index
        response = get_ecs_client().describe_container_instances(
            cluster=cluster_name,
            containerInstances=batch,
        )
        for instance in response['containerInstances']:
            instance_arn = dt_str(instance, 'containerInstanceArn')
            ec2_instance_id = dt_str(instance, 'ec2InstanceId')
            vpc_id = ''
            subnet_id = ''
            for attribute in instance['attributes']:
                if attribute.get('name') == 'ecs.vpc-id':
                    vpc_id = attribute.get('value')
                elif attribute.get('name') == 'ecs.subnet-id':
                    subnet_id = attribute.get('value')
            ret[instance_arn] = (ec2_instance_id, vpc_id, subnet_id,)
    return ret


def load_ec2_host_ip_by_info(
        container_instance_to_ec2_info: Dict[str, Tuple[str, str, str]]
) -> Dict[str, str]:
    """Get the host IP by the ec2 instance ID."""
    ec2_instance_id_info: Dict[str, Tuple[str, str, str, str]] = {
        ec2_info[0]: (container_arn, ec2_info[0], ec2_info[1], ec2_info[2],)
        for container_arn, ec2_info in container_instance_to_ec2_info.items()
    }
    ret: Dict[str, str] = {}
    paginator = get_ec2_client().get_paginator('describe_instances')
    response_iterator = paginator.paginate(
        InstanceIds=list(ec2_instance_id_info.keys()),
    )
    for page in response_iterator:
        for reservations in page['Reservations']:
            for ec2_instance in reservations['Instances']:
                ec2_instance_id = dt_str(ec2_instance, 'InstanceId')
                container_arn, _, vpc_id, subnet_id = ec2_instance_id_info[ec2_instance_id]
                # match up the network interface with the vpc and subnet...
                for network in ec2_instance['NetworkInterfaces']:
                    if (
                            (not vpc_id or dt_str(network, 'VpcId') == vpc_id) and
                            (not subnet_id or dt_str(network, 'SubnetId') == subnet_id)
                    ):
                        ret[container_arn] = dt_str(network, 'PrivateIpAddress')
                if container_arn not in ret:
                    ret[container_arn] = dt_str(ec2_instance, 'PrivateIpAddress')
    return ret


def add_taskdef_tags(tasks: Iterable[EcsTask]) -> None:
    """Add all taskdef defined tags to the tasks, but only if the task itself doesn't
    set that tag."""
    taskdef_envs: Dict[str, Dict[str, str]] = {}
    taskdef_tags: Dict[str, Dict[str, str]] = {}

    for task in tasks:
        if task.taskdef_arn not in taskdef_tags:
            tags, envs = load_taskdef_tags_env(task.taskdef_arn)
            taskdef_tags[task.taskdef_arn] = tags
            taskdef_envs[task.taskdef_arn] = envs
        task.taskdef_tags.update(taskdef_tags[task.taskdef_arn])
        task.taskdef_env.update(taskdef_envs[task.taskdef_arn])


def load_taskdef_tags_env(
        taskdef_arn: str,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Load the tags and env values for the given taskdef arns."""

    res = get_ecs_client().describe_task_definition(
        taskDefinition=taskdef_arn,
        include=['TAGS'],
    )
    env: Dict[str, str] = {}
    # Join all the container envs together.
    for container in res['taskDefinition']['containerDefinitions']:
        # NOTE: Ignores environmentFiles
        for val in container.get('environment', []):
            env[dt_str(val, 'name')] = dt_str(val, 'value')
    tags = {
        # Note: 'key' here.
        dt_str(tag, 'key'): dt_str(tag, 'value')
        for tag in res['tags']
    }
    return tags, env


# ---------------------------------------------------------------------------
CLIENTS: Dict[str, object] = {}
CONFIG: Dict[str, str] = {}


def set_aws_config(config: Dict[str, str]) -> None:
    """Set the global AWS configuration."""
    CONFIG.clear()
    CONFIG.update(config)


def get_ecs_client() -> Any:
    """Get the boto3 ecs client."""
    client_name = 'ecs'
    if client_name not in CLIENTS:
        session = get_session()
        CLIENTS[client_name] = session.client(client_name, config=Config(
            max_pool_connections=1,
            retries=dict(max_attempts=2)
        ))
    return CLIENTS[client_name]


def get_ec2_client() -> Any:
    """Get the boto3 ec2 client."""
    client_name = 'ec2'
    if client_name not in CLIENTS:
        session = get_session()
        CLIENTS[client_name] = session.client(client_name, config=Config(
            max_pool_connections=1,
            retries=dict(max_attempts=2)
        ))
    return CLIENTS[client_name]


def get_session() -> boto3.session.Session:
    """Create the AWS session for ECS clients."""
    region = CONFIG.get('AWS_REGION', None)
    profile = CONFIG.get('AWS_PROFILE', None)
    params: Dict[str, str] = {}
    if region:
        params['region_name'] = region
    if profile:
        params['profile_name'] = profile
    return boto3.session.Session(**params)  # type: ignore


def dt_get(inp: Dict[str, Any], *keys: Union[str, int]) -> Any:
    """Typed dictionary get"""
    current: Union[List[Any], Dict[str, Any]] = inp
    for k in keys:
        # Ignore the type here, because it *should* be an int -> list
        # and str -> dict.  The dict can take an int argument, but the
        # list can't, and will generate an index error.
        try:
            current = current[k]  # type: ignore
        except TypeError:
            raise ValueError('unexpected key {0} in {1}'.format(k, current))
        except IndexError:
            raise ValueError('unexpected key {0} in {1}'.format(k, current))
        except KeyError:
            raise ValueError('unexpected key {0} in {1}'.format(k, current))
    return current


def dt_opt_get(inp: Dict[str, Any], *keys: Union[str, int]) -> Any:
    """Typed dictionary get"""
    try:
        return dt_get(inp, *keys)
    except ValueError:
        return None


def dt_str(inp: Dict[str, Any], *keys: Union[str, int]) -> str:
    """Typed dictionary get"""
    val = dt_get(inp, *keys)
    assert isinstance(val, str)
    return val


def dt_opt_str(inp: Dict[str, Any], *keys: Union[str, int]) -> Optional[str]:
    """Typed dictionary get"""
    val = dt_opt_get(inp, *keys)
    assert val is None or isinstance(val, str)
    return val


def dt_int(inp: Dict[str, Any], *keys: Union[str, int]) -> int:
    """Typed dictionary get"""
    val = dt_get(inp, *keys)
    assert isinstance(val, int)
    return val
