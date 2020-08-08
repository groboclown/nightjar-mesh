
"""AWS ECS Interface."""

from typing import Dict, Tuple, List, Optional, Iterable, Set, Literal, Union, Any
import re
import json
import boto3
# from botocore.exceptions import ClientError  # type: ignore
from botocore.config import Config  # type: ignore
from .warn import warning, debug


RouteProtection = Literal['public', 'private']
PROTECTION_PUBLIC: RouteProtection = 'public'
PROTECTION_PRIVATE: RouteProtection = 'private'


PROTOCOL__HTTP1_1 = 'HTTP1.1'
PROTOCOL__HTTP2 = 'HTTP2'
SUPPORTED_PROTOCOLS = (
    PROTOCOL__HTTP1_1,
    PROTOCOL__HTTP2,
)

# This must be kept in-sync with the documentation
#  discovery-aws-ecs-task-tags.md
TAG__ROUTE_MATCHER = re.compile(r'^NJ_ROUTE_(\d+)$')
TAG__NAMESPACE_PORT_MATCHER = re.compile(r'^NJ_NAMESPACE_PORT_(\d+)$')

TAG__MODE = 'NJ_PROXY_MODE'
TAG__SERVICE = 'NJ_SERVICE'
TAG__COLOR = 'NJ_COLOR'
TAG__NAMESPACE = 'NJ_NAMESPACE'
TAG__PROTOCOL = 'NJ_PROTOCOL'
TAG__ROUTE_PORT = 'NJ_ROUTE_PORT'
TAG__ROUTE_PORT_INDEX_PREFIX = 'NJ_ROUTE_PORT_'
TAG__ROUTE_WEIGHT_INDEX_PREFIX = 'NJ_ROUTE_WEIGHT_'
TAG__PREFER_GATEWAY = 'NJ_PREFER_GATEWAY'

# A valid port number, but generally one that isn't listed on.
# This is to allow the map generation to work.
DEFAULT_ROUTE_PORT = 1


class RouteInfo:
    """Basic route info, parsed from the NJ_ROUTE_() value."""
    __slots__ = (
        'is_public_path', 'is_private_path', 'is_route_data', 'data',
        'index', 'container_port', 'host_port', 'weight',
    )
    data: Union[str, Dict[str, Any]]

    def __init__(
            self, index: int, route_value: str, container_port: str, host_port: int, weight: int,
    ) -> None:
        self.index = index
        self.container_port = container_port
        self.host_port = host_port
        self.weight = weight

        if route_value[0] == '!':
            self.is_public_path = False
            self.is_private_path = True
            self.is_route_data = False
            self.data = route_value[1:]
        elif route_value[0] == '+':
            self.is_public_path = True
            self.is_private_path = False
            self.is_route_data = False
            self.data = route_value[1:]
        elif route_value[0] == '{':
            self.is_public_path = False
            self.is_private_path = False
            self.is_route_data = True
            try:
                self.data = json.loads(route_value)
            except (ValueError, TypeError) as err:
                warning(
                    'Route Definition',
                    '{data} is not a valid JSON data structure: {error}',
                    data=route_value,
                    error=repr(err),
                )
                self.is_route_data = False
                self.data = ''
        else:
            self.is_public_path = True
            self.is_private_path = False
            self.is_route_data = False
            self.data = route_value

    def __repr__(self) -> str:
        return (
            'RouteInfo(index={index}, weight={weight}, data={data}, '
            'container_port={container_port}, host_port={host_port}, '
            'is_public_path={is_public_path}, is_private_path={is_private_path}, '
            'is_route_data={is_route_data})'
        ).format(
            is_public_path=self.is_public_path,
            is_private_path=self.is_private_path,
            is_route_data=self.is_route_data,
            data=repr(self.data),
            index=self.index,
            container_port=self.container_port,
            host_port=self.host_port,
            weight=self.weight,
        )


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
        # This is a bit complex, but done for consistent unit tests.
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

    def get_namespace_tag(self) -> Optional[str]:
        """Get the namespace tag, if it is provided."""
        return self.get_tag(TAG__NAMESPACE)

    def get_service_tag(self) -> Optional[str]:
        """Get the service tag, if it is provided."""
        return self.get_tag(TAG__SERVICE)

    def get_color_tag(self) -> Optional[str]:
        """Get the color tag, if it is provided"""
        return self.get_tag(TAG__COLOR)

    def get_protocol_tag(self) -> Optional[str]:
        """Get the protocol tag, if it is provided"""
        return self.get_tag(TAG__PROTOCOL)

    def get_prefer_gateway_tag(self) -> Optional[str]:
        """Get the prefer gateway tag, if provided"""
        return self.get_tag(TAG__PREFER_GATEWAY)

    def get_service_color_config(self) -> Optional[Tuple[str, str, str]]:
        """Returns None if this is not a service, or the namespace, service, color of it."""
        proxy_mode = self.get_tag(TAG__MODE)
        namespace = self.get_namespace_tag()
        service = self.get_service_tag()
        color = self.get_color_tag()
        if proxy_mode == 'SERVICE' and namespace and service and color:
            return namespace, service, color
        return None

    def get_gateway_config(self) -> Optional[str]:
        """Returns None if this is not a gateway, or the namespace of the gateway"""
        proxy_mode = self.get_tag(TAG__MODE)
        namespace = self.get_namespace_tag()
        if proxy_mode == 'GATEWAY' and namespace:
            return namespace
        return None

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

    def get_route_container_host_port_for(self, index: int) -> Tuple[str, int]:
        """Finds the (container) PORT value for the index, and grabs the
        mapped-to host port.  If no PORT is given, or the container port
        is not found, then the first host port is used.  If nothing valid
        is found, then this returns 1.

        The NJ_ROUTE_PORT_* value can be `container-name:port`, to allow for
        differentiating between containers that share the same container port.
        That value will be returned as the container port.

        Returns (container port, host port).  Container port is 0 if it is
            not a valid value.
        """
        container_port_str = self.get_tag(TAG__ROUTE_PORT_INDEX_PREFIX + str(index))
        if not container_port_str:
            # Try the generic one.
            container_port_str = self.get_tag(TAG__ROUTE_PORT)
        if not container_port_str:
            # Return the first host port.  If it isn't an integer,
            # then the default value is returned.
            for container_port_str, host_port in self.container_host_ports.items():
                if len(self.container_host_ports) > 1:
                    warning(
                        'TaskDef ' + self.task_arn,
                        'could not identify a unique published port; using {host_port}',
                        host_port=host_port,
                    )
                return container_port_str, host_port
            # No port known.  Return a value that isn't valid, but won't cause an error.
            warning(
                'TaskDef ' + self.task_arn,
                'could not find any published port.',
            )
            return '0', DEFAULT_ROUTE_PORT
        host_port = self.container_host_ports.get(container_port_str, DEFAULT_ROUTE_PORT)
        if host_port == DEFAULT_ROUTE_PORT:
            warning(
                'TaskDef ' + self.task_arn,
                'could not find a published port defined by {env1} or {env2} (set to {value}).',
                env1=TAG__ROUTE_PORT_INDEX_PREFIX + str(index),
                env2=TAG__ROUTE_PORT,
                value=container_port_str,
            )
        return container_port_str, host_port

    def get_route_weight(self, index: int) -> int:
        """Get the route index's weight, or default to 1."""
        try:
            weight = int(self.get_tag_with(TAG__ROUTE_WEIGHT_INDEX_PREFIX + str(index), '1'))
        except ValueError:
            weight = 1
        return max(1, weight)

    def get_routes(self) -> List[RouteInfo]:
        """Find all the route information."""
        ret: List[RouteInfo] = []
        for tag_name, tag_value in self.get_tags().items():
            match = TAG__ROUTE_MATCHER.match(tag_name)
            if match:
                try:
                    index = int(match.group(1))
                except ValueError:  # pragma no cover
                    # Because of the regular expression, this shouldn't happen...
                    continue  # pragma no cover
                container_port_str, host_port = self.get_route_container_host_port_for(index)
                ret.append(RouteInfo(
                    index, tag_value, container_port_str, host_port,
                    self.get_route_weight(index),
                ))
        return ret

    def get_namespace_egress_ports(self) -> Iterable[Tuple[str, int]]:
        """Create the namespace:port list"""
        ret: List[Tuple[str, int]] = []
        for tag_name, tag_value in self.get_tags().items():
            if TAG__NAMESPACE_PORT_MATCHER.match(tag_name):
                parts = tag_value.split(':', 1)
                if len(parts) != 2:
                    continue
                namespace, port_str = parts
                try:
                    port = int(port_str)
                except ValueError:
                    continue
                ret.append((namespace, port))
        return ret


def load_mesh_tasks(
        cluster_names: Iterable[str],
        required_tag_name: Optional[str],
        required_tag_value: Optional[str],
) -> Iterable[EcsTask]:
    """
    Find tasks that match up to the requirements for this configuration.  They can
    be in any namespace.
    """
    ret: List[EcsTask] = []
    for cluster_name in cluster_names:
        ret.extend(filter_tasks(
            load_tasks_for_cluster(cluster_name),
            required_tag_name,
            required_tag_value,
        ))
    return ret


def filter_tasks(
        tasks: Iterable[EcsTask],
        required_tag_name: Optional[str],
        required_tag_value: Optional[str],
) -> Iterable[EcsTask]:
    """Filter out tasks that do not meet the requirements for being in the mesh."""
    ret: List[EcsTask] = []
    for task in tasks:
        if required_tag_name:
            value = task.get_tag(required_tag_name)
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

        # Must be either a valid gateway or service-color.
        if task.get_gateway_config() or task.get_service_color_config():
            debug('filter_tasks', 'Using task {task}', task=task)
            ret.append(task)
        else:
            debug('filter_tasks', 'Omitting task {task}', task=task)
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
    debug(
        'get_task_arns_in_cluster',
        'Cluster {name} has task arns {tasks}', name=cluster_name, tasks=ret,
    )
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

            task = EcsTask(
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
            )
            # debug('load_tasks_by_arns', 'Constructed {task}', task=task)
            discovered_tasks.append(task)
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
                            (not vpc_id or dt_opt_str(network, 'VpcId') == vpc_id) and
                            (not subnet_id or dt_opt_str(network, 'SubnetId') == subnet_id)
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
    CLIENTS.clear()
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
