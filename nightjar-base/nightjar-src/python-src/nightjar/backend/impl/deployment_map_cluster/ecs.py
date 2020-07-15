
from typing import Dict, Tuple, List, Optional, Iterable, Union, Any
import re
import boto3
from botocore.exceptions import ClientError  # type: ignore
from botocore.config import Config  # type: ignore
from .config import AwsEcsClusterConfig
from ....protect import PROTECTION_PRIVATE, PROTECTION_PUBLIC, RouteProtection


PROTOCOL__HTTP1_1 = 'HTTP1.1'
PROTOCOL__HTTP2 = 'HTTP2'
SUPPORTED_PROTOCOLS = (
    PROTOCOL__HTTP1_1,
    PROTOCOL__HTTP2,
)

ROUTE_TAG_MATCHER = re.compile(r'^ROUTE_(\d+)$')


class EcsTask:
    def __init__(
            self,
            task_name: str,
            task_arn: str,
            taskdef_arn: str,
            instance_arn: str,
            host_ip: str,
            container_host_ports: Dict[str, int],
            tags: Dict[str, str]
    ) -> None:
        self.task_name = task_name
        self.task_arn = task_arn
        self.taskdef_arn = taskdef_arn
        self.instance_arn = instance_arn
        self.host_ip = host_ip
        self.container_host_ports = dict(container_host_ports)
        self.tags = dict(tags)

    def get_namespace_tag(self) -> Optional[str]:
        return self.tags.get('NAMESPACE')

    def get_protocol(self) -> str:
        protocol = self.tags.get('PROTOCOL', PROTOCOL__HTTP1_1)
        if protocol.upper() in SUPPORTED_PROTOCOLS:
            return protocol.upper()
        return PROTOCOL__HTTP1_1

    def get_service_name(self) -> str:
        return self.get_service_name_tag() or self.task_name

    def get_service_name_tag(self) -> Optional[str]:
        return self.tags.get('SERVICE_NAME')

    def get_color(self) -> str:
        return self.tags.get('COLOR') or 'default'

    def get_service_id(self) -> str:
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
        container_port_str = self.tags.get('PORT_' + str(index))
        if not container_port_str:
            container_port_str = self.tags.get('PORT')
        if not container_port_str:
            # Return the first host port.  If it isn't an integer,
            # then the default value is returned.
            for container_port_str, host_port in self.container_host_ports.items():
                return container_port_str, host_port
            # No port known.  Return a value that isn't valid, but won't cause an error.
            return '0', 1
        else:
            host_port = self.container_host_ports.get(container_port_str, 1)
            return container_port_str, host_port

    def get_route_weight_protection_for(self, index: int) -> Tuple[Optional[str], int, RouteProtection]:
        route = self.tags.get('ROUTE_' + str(index))
        if not route:
            return None, 0, PROTECTION_PRIVATE
        protection = PROTECTION_PUBLIC
        if route[0] == '!':
            route = route[1:]
            protection = PROTECTION_PRIVATE
        weight_str = self.tags.get('WEIGHT_' + str(index))
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
        for tag_name in self.tags.keys():
            match = ROUTE_TAG_MATCHER.match(tag_name)
            if match:
                try:
                    index = int(match.group(1))
                    ret.append(index)
                except ValueError:
                    pass
        return ret


def load_tasks_for_namespace(namespace: str) -> Iterable[EcsTask]:
    """
    Find tasks that match up to the requirements for this configuration.
    """
    ret: List[EcsTask] = []
    if not CONFIG:
        return []
    for cluster_name in CONFIG.cluster_names:
        for task in load_tasks_for_cluster(cluster_name):
            if CONFIG.required_tag_name:
                if CONFIG.required_tag_name in task.tags:
                    value = task.tags['value']
                    if CONFIG.required_tag_value and value != CONFIG.required_tag_value:
                        continue
                    # If no value is required, then we don't check it.
                else:
                    continue
            if task.get_namespace_tag() != namespace or not task.get_color():
                continue
            ret.append(task)
    return ret


def load_tasks_for_cluster(cluster_name: str) -> Iterable[EcsTask]:
    """
    Runs ListTasks on the cluster, then runs DescribeTasks to get the details.
    """
    return load_tasks_by_arns(cluster_name, get_task_arns_in_cluster(cluster_name))


def get_task_arns_in_cluster(cluster_name: str) -> Iterable[str]:
    ret: List[str] = []
    paginator = get_ecs_client().get_paginator('list_tasks')
    response_iterator = paginator.paginate(cluster=cluster_name)
    for page in response_iterator:
        for task_arn in page['taskArns']:
            ret.append(task_arn)
    return ret


def load_tasks_by_arns(cluster_name: str, task_arns: Iterable[str]) -> List[EcsTask]:
    """
    Reads the definition for these tasks.
    """
    # Can query up to 100 task arns per request.
    all_task_arns = list(set(task_arns))
    discovered_tasks: List[EcsTask] = []
    index = 0

    while index < len(all_task_arns):
        next_index = min(index + 100, len(all_task_arns))
        batch = all_task_arns[index:next_index]
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
        for task in response['tasks']:
            service_name = ''
            for container in task['containers']:
                container_name = dt_str(container, 'name')
                if not service_name:
                    service_name = container_name
                for binding in container['networkBindings']:
                    # Ignore all but 'tcp' protocols.
                    if dt_str(binding, 'protocol') != 'tcp':
                        continue
                    # If there's an overlap with an existing registration, overwrite it.
                    container_port = dt_int(binding, 'containerPort')
                    host_port = dt_int(binding, 'hostPort')
                    container_host_ports['{0}:{1}'.format(container_name, container_port)] = host_port
                    container_host_ports[str(container_port)] = host_port
            discovered_tasks.append(EcsTask(
                task_name=service_name,
                task_arn=dt_str(task, 'taskArn'),
                taskdef_arn=dt_str(task, 'taskDefinitionArn'),
                instance_arn=dt_str(task, 'containerInstanceArn'),
                host_ip='',
                container_host_ports=container_host_ports,
                tags=dict([
                    (dt_str(tag, 'key'), dt_str(tag, 'value'),)
                    for tag in task['tags']
                ])
            ))

    # Map the task container instances to the ec2 host IP.
    # TODO THIS IS NOT WRITTEN WITH FARGATE IN MIND.  NEEDS TO BE UPDATED
    #   TO WORK WITH FARGATE.
    container_instance_to_ip = load_ec2_host_ip_by_info(
        load_ec2_info_by_container_instances(
            cluster_name,
            [
                task.instance_arn
                for task in discovered_tasks
            ],
        ),
    )
    ret: List[EcsTask] = []
    for task in discovered_tasks:
        # Note: there's a potential timing condition here, where an EC2 instance
        # dropped between when we queried for a task and when we queried for the
        # ec2 instance.  So it might not be present.
        if task.instance_arn and task.instance_arn in container_instance_to_ip:
            task.host_ip = container_instance_to_ip[task.instance_arn]
            ret.append(task)
    return ret


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
                    subnet_id = attribute.get('ecs.subnet-id')
            ret[instance_arn] = (ec2_instance_id, vpc_id, subnet_id,)
    return ret


def load_ec2_host_ip_by_info(
        container_instance_to_ec2_info: Dict[str, Tuple[str, str, str]]
) -> Dict[str, str]:
    ec2_instance_id_info: Dict[str, Tuple[str, str, str, str]] = dict([
        (ec2_info[0], (container_arn, ec2_info[0], ec2_info[1], ec2_info[2],))
        for container_arn, ec2_info in container_instance_to_ec2_info.items()
    ])
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
                        # TODO include ipv6 ('Ipv6Addresses')
                        ret[container_arn] = dt_str(network, 'PrivateIpAddress')
    return ret


# ---------------------------------------------------------------------------
CLIENTS: Dict[str, object] = {}
CONFIG: Optional[AwsEcsClusterConfig] = None


def set_aws_config(config: AwsEcsClusterConfig) -> None:
    global CONFIG
    CONFIG = config


def get_ecs_client() -> Any:
    client_name = 'ecs'
    if client_name not in CLIENTS:
        region = CONFIG and CONFIG.aws_region or None
        profile = CONFIG and CONFIG.aws_profile or None
        session = boto3.session.Session(
            region_name=region,  # type: ignore
            profile_name=profile,  # type: ignore
        )
        CLIENTS[client_name] = session.client(client_name, config=Config(
            max_pool_connections=1,
            retries=dict(max_attempts=2)
        ))
    return CLIENTS[client_name]


def get_ec2_client() -> Any:
    client_name = 'ec2'
    if client_name not in CLIENTS:
        region = CONFIG and CONFIG.aws_region or None
        profile = CONFIG and CONFIG.aws_profile or None
        session = boto3.session.Session(
            region_name=region,  # type: ignore
            profile_name=profile,  # type: ignore
        )
        CLIENTS[client_name] = session.client(client_name, config=Config(
            max_pool_connections=1,
            retries=dict(max_attempts=2)
        ))
    return CLIENTS[client_name]


def dt_get(d: Dict[str, Any], *keys: Union[str, int]) -> Any:
    current: Union[List[Any], Dict[str, Any]] = d
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


def dt_opt_get(d: Dict[str, Any], *keys: Union[str, int]) -> Any:
    try:
        return dt_get(d, *keys)
    except ValueError:
        return None


def dt_str(d: Dict[str, Any], *keys: Union[str, int]) -> str:
    val = dt_get(d, *keys)
    assert isinstance(val, str)
    return val


def dt_opt_str(d: Dict[str, Any], *keys: Union[str, int]) -> Optional[str]:
    val = dt_opt_get(d, *keys)
    assert val is None or isinstance(val, str)
    return val


def dt_int(d: Dict[str, Any], *keys: Union[str, int]) -> int:
    val = dt_get(d, *keys)
    assert isinstance(val, int)
    return val


def dt_list_dict(d: Dict[str, Any], *keys: Union[str, int]) -> List[Dict[str, Any]]:
    val = dt_get(d, *keys)
    assert isinstance(val, list)
    return list(val)


def dt_dict(d: Dict[str, Any], *keys: Union[str, int]) -> Dict[str, Any]:
    val = dt_get(d, *keys)
    assert isinstance(val, dict)
    return val
