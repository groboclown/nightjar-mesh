#!/usr/bin/python3


from typing import List, Tuple, Dict, Optional, Union, Any
import os
import sys
import datetime
import boto3
from botocore.exceptions import ClientError
import json


MAX_NAMESPACE_COUNT = 99
SERVICE_SETTINGS_INSTANCE_ID = 'service-settings'
SERVICE_NAME_ATTRIBUTE_KEY = 'SERVICE'
COLOR_NAME_ATTRIBUTE_KEY = 'COLOR'
USES_HTTP2_ATTRIBUTE_KEY = 'HTTP2'
USES_HTTP2_AFFIRMATIVE_VALUES = (
    'yes', 'true', 'enabled', 'active', '1', 'http2',
)
SERVICE_MEMBER_GATEWAY = '-gateway-'
DEFAULT_SERVICE_PORT = '8080'
REQUIRE_REFRESH_LIMIT = datetime.timedelta(minutes=2)

# Service instance well-defined custom attributes
ATTR_AVAILABILITY_ZONE = 'AVAILABILITY_ZONE'
ATTR_AWS_INIT_HEALTH_STATUS = 'AWS_INIT_HEALTH_STATUS'
ATTR_EC2_INSTANCE_ID = 'EC2_INSTANCE_ID'
ATTR_AWS_INSTANCE_IPV4 = 'AWS_INSTANCE_IPV4'
ATTR_ECS_CLUSTER_NAME = 'ECS_CLUSTER_NAME'
ATTR_ECS_SERVICE_NAME = 'ECS_SERVICE_NAME'
ATTR_AWS_INSTANCE_PORT = 'AWS_INSTANCE_PORT'
ATTR_ECS_TASK_DEFINITION_FAMILY = 'ECS_TASK_DEFINITION_FAMILY'
ATTR_REGION = 'REGION'
AWS_STANDARD_ATTRIBUTES = (
    ATTR_AVAILABILITY_ZONE,
    ATTR_AWS_INIT_HEALTH_STATUS,
    ATTR_EC2_INSTANCE_ID,
    ATTR_AWS_INSTANCE_IPV4,
    ATTR_ECS_CLUSTER_NAME,
    ATTR_ECS_SERVICE_NAME,
    ATTR_AWS_INSTANCE_PORT,
    ATTR_ECS_TASK_DEFINITION_FAMILY,
    ATTR_REGION,
)


# ---------------------------------------------------------------------------
class DiscoveryServiceInstance:
    def __init__(self, instance_id: str, attributes: Dict[str, str]) -> None:
        self.instance_id = instance_id
        self.attributes = dict(attributes)
        self.cache_load_time = datetime.datetime.now()
        self.ec2_instance_id = attributes.get(ATTR_EC2_INSTANCE_ID)
        self.ipv4 = attributes.get(ATTR_AWS_INSTANCE_IPV4)
        self.port_str = attributes.get(ATTR_AWS_INSTANCE_PORT, '0')


class DiscoveryServiceColor:
    instances: List[DiscoveryServiceInstance]
    group_service_name: Optional[str]
    group_color_name: Optional[str]
    path_weights: Dict[str, int]
    cache_load_time: Optional[datetime.datetime]

    def __init__(
            self, arn: str, namespace_id: str, service_id: str, discovery_service_name: str
    ) -> None:
        self.service_arn = arn
        self.namespace_id = namespace_id
        self.service_id = service_id
        self.discovery_service_name = discovery_service_name
        self.instances = []
        self.path_weights = {}

        # The service association
        self.group_service_name = None
        self.group_color_name = None
        self.uses_http2 = False

        self.cache_load_time = None

    def load_instances(self, refresh_cache: bool) -> None:
        if _skip_reload(self.cache_load_time, refresh_cache):
            return
        group_service_name: Optional[str] = self.group_service_name
        group_color_name: Optional[str] = self.group_color_name
        path_weights: Dict[str, int] = {}
        instances: List[DiscoveryServiceInstance] = []

        client = get_servicediscovery_client()
        paginator = client.get_paginator('list_instances')
        page_iterator = paginator.paginate(ServiceId=self.service_id)
        try:
            for page in page_iterator:
                for instance in dt_list_dict(page, 'Instances'):
                    # instance ID is the assigned-to name of the instance, which is unique only for the
                    # service.
                    instance_id = dt_str(instance, 'Id')
                    attributes = dt_dict(instance, 'Attributes')
                    if instance_id == SERVICE_SETTINGS_INSTANCE_ID:
                        # This is the special instance registration to define the
                        # data for this service.
                        for key, value in attributes.items():
                            if key == SERVICE_NAME_ATTRIBUTE_KEY:
                                group_service_name = value.strip()
                            elif key == COLOR_NAME_ATTRIBUTE_KEY:
                                group_color_name = value.strip()
                            elif key == USES_HTTP2_ATTRIBUTE_KEY:
                                self.uses_http2 = value.strip().lower() in USES_HTTP2_AFFIRMATIVE_VALUES
                            elif key not in AWS_STANDARD_ATTRIBUTES and key[0] in '/?*':
                                try:
                                    weight = int(value.strip())
                                except ValueError:
                                    _warn(
                                        "Not integer path weight for service {s}, instance {i}, path {p}, value [{v}]",
                                        s=self.service_id,
                                        i=instance_id,
                                        p=key,
                                        v=value,
                                    )
                                    weight = 1
                                path_weights[key.strip()] = weight
                    else:
                        instances.append(DiscoveryServiceInstance(instance_id, attributes))
        except ClientError as e:
            # This means that either there was a communication error, or the
            # service was deleted during the query.
            # Clear out the instances and weights, since they can no longer be trusted.
            _warn('Failed to load instances for service {svc}: {e}', svc=self.service_id, e=e)
            instances = []
            path_weights = {}
        self.group_service_name = group_service_name
        self.group_color_name = group_color_name
        self.path_weights = path_weights
        self.instances = instances
        self.cache_load_time = datetime.datetime.now()

    def load_namespace(self, listen_port: int) -> 'DiscoveryServiceNamespace':
        client = get_servicediscovery_client()
        raw = client.get_namespace(Id=self.namespace_id)
        return DiscoveryServiceNamespace.from_resp(listen_port, raw)

    @staticmethod
    def from_resp(resp: Dict[str, Any]) -> 'DiscoveryServiceColor':
        # _note("Fetched discovery service {0}", resp)
        if 'Service' in resp:
            resp = resp['Service']
        arn = dt_str(resp, 'Arn')
        namespace_id = dt_str(resp, 'NamespaceId')
        service_id = dt_str(resp, 'Id')
        discovery_service_name = dt_str(resp, 'Name')
        # Skip description, health check config, and other things.
        return DiscoveryServiceColor(arn, namespace_id, service_id, discovery_service_name)

    @staticmethod
    def from_resp_list(resp: Dict[str, Any], namespace_id: str) -> List['DiscoveryServiceColor']:
        ret: List[DiscoveryServiceColor] = []
        for raw in dt_list_dict(resp, 'Services'):
            raw['NamespaceId'] = namespace_id
            ret.append(DiscoveryServiceColor.from_resp(raw))
        return ret

    @staticmethod
    def from_single_id(service_id: str) -> Optional['DiscoveryServiceColor']:
        client = get_servicediscovery_client()
        try:
            return DiscoveryServiceColor.from_resp(client.get_service(Id=service_id))
        except ClientError as e:
            _warn('Could not find service discovery service with id {svc}: {e}', svc=repr(service_id), e=e)
            return None


class DiscoveryServiceNamespace:
    services: List[DiscoveryServiceColor]
    cache_load_time: Optional[datetime.datetime]

    def __init__(
            self,
            namespace_port: int,
            namespace_id: str,
            namespace_arn: str,
            namespace_type: str,
            namespace_name: str,
            hosted_zone_id: Optional[str],
            http_name: Optional[str],
    ) -> None:
        self.namespace_id = namespace_id
        self.namespace_port = namespace_port
        self.namespace_arn = namespace_arn
        self.namespace_type = namespace_type
        self.namespace_name = namespace_name

        # The ID for the Route 53 hosted zone that AWS Cloud Map creates when you create a namespace.
        self.hosted_zone_id = hosted_zone_id

        # The name of an HTTP namespace.
        self.http_name = http_name

        self.services = []
        self.cache_load_time = None

    def load_services(self, refresh_cache: bool) -> None:
        if _skip_reload(self.cache_load_time, refresh_cache):
            return
        client = get_servicediscovery_client()

        service_paginator = client.get_paginator('list_services')
        service_iter = service_paginator.paginate(
            Filters=[{
                'Name': 'NAMESPACE_ID',
                'Values': [self.namespace_id],
                'Condition': 'EQ'
            }]
        )
        self.services = []
        for service_list_raw in service_iter:
            for service in DiscoveryServiceColor.from_resp_list(service_list_raw, self.namespace_id):
                service.load_instances(True)
                self.services.append(service)

        self.cache_load_time = datetime.datetime.now()

    @staticmethod
    def from_resp(port: int, resp: Dict[str, Any]) -> 'DiscoveryServiceNamespace':
        if 'Namespace' in resp:
            resp = dt_dict(resp, 'Namespace')
        namespace_id = dt_str(resp, 'Id')
        namespace_arn = dt_str(resp, 'Arn')
        namespace_name = dt_str(resp, 'Name')
        namespace_type = dt_str(resp, 'Type')
        # skip Description
        hosted_zone_id = dt_opt_str(resp, 'Properties', 'DnsProperties', 'HostedZoneId')
        http_name = dt_opt_str(resp, 'Properties', 'HttpProperties', 'HttpName')
        # service_count = dt_int(resp, 'ServiceCount')
        return DiscoveryServiceNamespace(
            namespace_port=port,
            namespace_id=namespace_id,
            namespace_arn=namespace_arn,
            namespace_type=namespace_type,
            namespace_name=namespace_name,
            hosted_zone_id=hosted_zone_id,
            http_name=http_name,
        )

    @staticmethod
    def load_namespaces(namespace_ports: Dict[str, int]) -> List['DiscoveryServiceNamespace']:
        ret: List['DiscoveryServiceNamespace'] = []
        remaining = set(namespace_ports.keys())
        client = get_servicediscovery_client()
        paginator = client.get_paginator('list_namespaces')
        for page in paginator.paginate():
            for raw in dt_list_dict(page, 'Namespaces'):
                ns = DiscoveryServiceNamespace.from_resp(-1, raw)
                if ns.namespace_id in remaining:
                    remaining.remove(ns.namespace_id)
                    ns.namespace_port = namespace_ports[ns.namespace_id]
                    ret.append(ns)
                elif ns.namespace_arn in remaining:
                    remaining.remove(ns.namespace_arn)
                    ns.namespace_port = namespace_ports[ns.namespace_arn]
                    ret.append(ns)
                elif ns.namespace_name in remaining:
                    remaining.remove(ns.namespace_name)
                    ns.namespace_port = namespace_ports[ns.namespace_name]
                    ret.append(ns)
        return ret


# ---------------------------------------------------------------------------
class LocalServiceSetup:
    service_color: Optional[DiscoveryServiceColor]
    cache_load_time: Optional[datetime.datetime]

    def __init__(
            self,
            service_member: str,
            service_member_port: int,
    ) -> None:
        self.service_member = service_member
        self.service_member_port = service_member_port
        self.service_color = None
        self.cache_load_time = None

    def load_service(self, refresh_cache: bool) -> None:
        if _skip_reload(self.cache_load_time, refresh_cache):
            return
        self.service_color = DiscoveryServiceColor.from_single_id(self.service_member)
        self.cache_load_time = datetime.datetime.now()

    @staticmethod
    def from_env() -> Optional['LocalServiceSetup']:
        member = os.environ.get('SERVICE_MEMBER', 'NOT_SET').strip()
        if member == 'NOT_SET':
            _fatal(
                'Must set SERVICE_MEMBER environment variable to the AWS Cloud Map (service discovery) service ID.'
            )
        if member.lower() == SERVICE_MEMBER_GATEWAY:
            _note("Using 'gateway' mode for the proxy.")
            return None

        port_str = os.environ.get('SERVICE_PORT', DEFAULT_SERVICE_PORT)
        valid_port, member_port = _validate_port(port_str)
        if not valid_port:
            _fatal(
                "Invalid port for service member ({port}) in SERVICE_PORT, cannot use proxy.",
                port=port_str
            )
        return LocalServiceSetup(member, member_port)


class EnvSetup:
    def __init__(
            self,
            admin_port: int,
            local_service: Optional[LocalServiceSetup],
            namespaces: Dict[str, int],
    ) -> None:
        self.admin_port = admin_port
        self.local_service = local_service
        self.namespace_ports = dict(namespaces)

    def get_loaded_namespaces(self) -> List[DiscoveryServiceNamespace]:
        """Includes the local service, if given."""
        np = dict(self.namespace_ports)
        if self.local_service:
            self.local_service.load_service(True)
            assert self.local_service.service_color is not None
            np[self.local_service.service_color.namespace_id] = self.local_service.service_member_port
        return DiscoveryServiceNamespace.load_namespaces(self.namespace_ports)

    @staticmethod
    def from_env() -> 'EnvSetup':
        admin_port_str = os.environ.get('ENVOY_ADMIN_PORT', '9901')
        admin_port_valid, admin_port = _validate_port(admin_port_str)
        if not admin_port_valid:
            _fatal(
                "Must set ENVOY_ADMIN_PORT to a valid port number; found {port}",
                port=admin_port_str
            )
        local_service = LocalServiceSetup.from_env()
        namespaces: Dict[str, int] = {}
        for ni in range(0, MAX_NAMESPACE_COUNT + 1):
            namespace = os.environ.get('NAMESPACE_{0}'.format(ni), '').strip()
            if namespace:
                namespace_port_str = os.environ.get('NAMESPACE_{0}_PORT'.format(ni), 'NOT SET')
                port_valid, port = _validate_port(namespace_port_str)
                if port_valid:
                    namespaces[namespace] = port
                else:
                    _warn(
                        'Namespace {index} ({name}) has invalid port value ({port}); skipping it.',
                        index=ni, name=namespace, port=namespace_port_str,
                    )

        return EnvSetup(admin_port, local_service, namespaces)


# ---------------------------------------------------------------------------
class EnvoyRoute:
    """
    Defines the URL path to cluster matching.
    """
    def __init__(self, path_prefix: str, cluster_weights: Dict[str, int], is_local_route: bool) -> None:
        if path_prefix[0] == '?':
            self.is_private = True
            self.path_prefix = path_prefix[1:]
        else:
            self.is_private = False
            self.path_prefix = path_prefix
        self.cluster_weights = cluster_weights
        self.total_weight = sum(cluster_weights.values())
        self.is_local_route = is_local_route

    def get_context(self) -> Optional[Dict[str, Any]]:
        # skip creation if:
        #  - this is a proxy to a non-local namespace
        #  - this is a private path.
        if not self.is_local_route and self.is_private:
            return None

        cluster_count = len(self.cluster_weights)
        if cluster_count <= 0:
            return None

        return {
            'route_path': self.path_prefix,
            'has_one_cluster': cluster_count == 1,
            'has_many_clusters': cluster_count > 1,
            'total_cluster_weight': self.total_weight,
            'clusters': [{
                'cluster_name': cn,
                'route_weight': cw,
            } for cn, cw in self.cluster_weights.items()],
        }


class EnvoyListener:
    """
    Defines a port listener in envoy, which corresponds to a namespace.
    """
    def __init__(self, port: int, routes: List[EnvoyRoute]) -> None:
        self.port = port
        self.routes = list(routes)

    def get_route_contexts(self) -> List[Dict[str, Any]]:
        ret: List[Dict[str, Any]] = []
        for route in self.routes:
            ctx = route.get_context()
            if ctx:
                ret.append(ctx)
        return ret

    def get_context(self) -> Dict[str, Any]:
        return {
            'mesh_port': self.port,
            'routes': self.get_route_contexts(),

            # TODO make this configurable
            'healthcheck_path': '/ping',
        }


class EnvoyCluster:
    """
    Defines a cluster within envoy.  It's already been weighted according to the path.
    """
    def __init__(
            self,
            cluster_name: str,
            uses_http2: bool,
            instances: List[DiscoveryServiceInstance]
    ) -> None:
        self.cluster_name = cluster_name
        self.uses_http2 = uses_http2
        self.instances = list(instances)

    def endpoint_count(self) -> int:
        return len(self.instances)

    def get_context(self) -> Dict[str, Any]:
        instances = self.instances
        if not instances:
            _note("No instances known for cluster {c}; creating temporary one.", c=self.cluster_name)
            instances = [DiscoveryServiceInstance('x', {
                # We need something here, otherwise the route will say the cluster doesn't exist.
                ATTR_AWS_INSTANCE_IPV4: '127.0.0.1',
                ATTR_AWS_INSTANCE_PORT: '99',
            })]
        return {
            'name': self.cluster_name,
            'uses_http2': self.uses_http2,
            'endpoints': [{
                'ipv4': inst.ipv4,
                'port': inst.port_str,
            } for inst in instances],
        }


class EnvoyConfig:
    def __init__(
            self,
            listeners: List[EnvoyListener], clusters: List[EnvoyCluster],
            network_name: str, service_member: str,
            admin_port: int
    ) -> None:
        self.listeners = listeners
        self.clusters = clusters
        self.network_name = network_name
        self.service_member = service_member
        self.admin_port = admin_port

    def get_context(self) -> Dict[str, Any]:
        if not self.listeners:
            _fatal('No listeners; cannot be a proxy.')
        cluster_endpoint_count = sum([c.endpoint_count() for c in self.clusters])
        return {
            'network_name': self.network_name,
            'service_member': self.service_member,
            'admin_port': self.admin_port,
            'listeners': [lt.get_context() for lt in self.listeners],
            'has_clusters': cluster_endpoint_count > 0,
            'clusters': [c.get_context() for c in self.clusters],
        }


# ---------------------------------------------------------------------------
def collate_ports_and_clusters(
        admin_port: int,
        namespaces: List[DiscoveryServiceNamespace], local: Optional[LocalServiceSetup],
        refresh_cache: bool
) -> EnvoyConfig:
    """
    Construct the listener groups, which are per namespace, and the clusters
    referenced by the listeners.

    The local service color group will redirect everything to that service
    to within the local container (as long as the paths reference this color).

    In order to support better envoy cluster traffic management, each
    service/color is its own cluster.
    """
    output_listeners: List[EnvoyListener] = []
    output_clusters: List[EnvoyCluster] = []
    is_local_route = False
    service_member = 'gateway'
    network_name = os.environ.get('NETWORK_NAME', None)

    if local:
        is_local_route = True
        local.load_service(refresh_cache)
        if local.service_color:
            service_member = '{0}-{1}'.format(
                local.service_color.group_service_name,
                local.service_color.group_color_name,
            )
            in_namespaces = False
            for namespace in namespaces:
                if namespace.namespace_id == local.service_color.namespace_id:
                    in_namespaces = True
                    network_name = network_name or namespace.namespace_id
                    break
            if not in_namespaces:
                namespaces.extend(DiscoveryServiceNamespace.load_namespaces({
                    local.service_color.namespace_id: local.service_member_port
                }))

    for namespace in namespaces:
        routes: Dict[str, Dict[str, int]] = {}
        namespace.load_services(refresh_cache)
        for service_color in namespace.services:
            service_color.load_instances(refresh_cache)
            if (
                    local
                    and (
                        local.service_member == service_color.service_id
                        or local.service_member == service_color.service_arn
                    )
            ):
                # The local service should never be in the envoy.
                pass
            else:
                if not service_color.instances:
                    _warn(
                        "Cluster {s}-{c} has no discovered instances",
                        s=service_color.group_service_name,
                        c=service_color.group_color_name
                    )
                cluster = EnvoyCluster(
                    '{0}-{1}'.format(service_color.group_service_name, service_color.group_color_name),
                    service_color.uses_http2,
                    service_color.instances
                )
                if service_color.path_weights:
                    output_clusters.append(cluster)
                    for path, weight in service_color.path_weights.items():
                        if path not in routes:
                            routes[path] = {}
                        routes[path][cluster.cluster_name] = weight
        envoy_routes: List[EnvoyRoute] = [
            EnvoyRoute(path, cluster_weights, is_local_route)
            for path, cluster_weights in routes.items()
        ]
        # Even if there are no routes, still add the listener.
        # During initialization, the dependent containers haven't started yet and may
        # require this proxy to be running before they start.
        listener = EnvoyListener(namespace.namespace_port, envoy_routes)
        output_listeners.append(listener)

    return EnvoyConfig(output_listeners, output_clusters, network_name or service_member, service_member, admin_port)


# ---------------------------------------------------------------------------
CLIENTS: Dict[str, object] = {}


def get_servicediscovery_client() -> Any:
    client_name = 'servicediscovery'
    if client_name not in CLIENTS:
        region = os.environ.get('AWS_REGION', None)
        profile = os.environ.get('AWS_PROFILE', None)
        session = boto3.session.Session(
            region_name=region,
            profile_name=profile,
        )
        CLIENTS[client_name] = session.client('servicediscovery')
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
        dt_get(d, *keys)
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


# ---------------------------------------------------------------------------
def _skip_reload(cache_load_time: Optional[datetime.datetime], refresh_cache: bool) -> bool:
    if not cache_load_time or refresh_cache:
        return False
    return datetime.datetime.now() - cache_load_time < REQUIRE_REFRESH_LIMIT


def _validate_port(port_str: str) -> Tuple[bool, int]:
    try:
        port = int(port_str)
    except ValueError:
        port = -1
    return 0 < port < 65536, port


def _note(msg: str, **args: Any) -> None:
    sys.stderr.write("NOTE: {0}\n".format(msg.format(**args)))


def _warn(msg: str, **args: Any) -> None:
    sys.stderr.write("WARNING: {0}\n".format(msg.format(**args)))


def _fatal(msg: str, **args: Any) -> None:
    # Fatal errors quit right away.
    raise Exception(msg.format(**args))


# ---------------------------------------------------------------------------
def main() -> str:
    env = EnvSetup.from_env()
    namespaces = env.get_loaded_namespaces()
    envoy_config = collate_ports_and_clusters(
        env.admin_port, namespaces, env.local_service, True
    )
    return json.dumps(envoy_config.get_context())


if __name__ == '__main__':
    main_stdout = main()
    print(main_stdout)
