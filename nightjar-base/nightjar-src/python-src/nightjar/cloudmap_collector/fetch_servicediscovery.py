#!/usr/bin/python3


from typing import List, Dict, Optional, Callable, TypeVar, Union, Any
import os
import time
import datetime
import re
import boto3
from botocore.exceptions import ClientError  # type: ignore
from botocore.config import Config  # type: ignore
from ..msg import warn

T = TypeVar('T')
# ARNs are in the form 'arn:aws:servicediscovery:(region):(account):namespace/(namespace)'
NAMESPACE_ARN_PATTERN = re.compile(r'^arn:aws:servicediscovery:[^:]+:[^:]+:namespace/(.*)$')

MAX_RETRY_COUNT = 5
SERVICE_SETTINGS_INSTANCE_ID = 'service-settings'
SERVICE_NAME_ATTRIBUTE_KEY = 'SERVICE'
COLOR_NAME_ATTRIBUTE_KEY = 'COLOR'
USES_HTTP2_ATTRIBUTE_KEY = 'HTTP2'
USES_HTTP2_AFFIRMATIVE_VALUES = (
    'yes', 'true', 'enabled', 'active', '1', 'http2',
)
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
        if skip_reload(self.cache_load_time, refresh_cache):
            return
        group_service_name: Optional[str] = self.group_service_name
        group_color_name: Optional[str] = self.group_color_name
        path_weights: Dict[str, int] = {}
        instances: List[DiscoveryServiceInstance] = []

        # API INVOCATIONS: service_color_count * (1 + floor(instance_count / 100))
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
                                    warn(
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
            warn('Failed to load instances for service {svc}: {e}', svc=self.service_id, e=e)
            instances = []
            path_weights = {}
        self.group_service_name = group_service_name
        self.group_color_name = group_color_name
        self.path_weights = path_weights
        self.instances = instances
        self.cache_load_time = datetime.datetime.now()

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
        # API INVOCATIONS: service_color_count * 1
        client = get_servicediscovery_client()
        try:
            return DiscoveryServiceColor.from_resp(client.get_service(Id=service_id))
        except ClientError as e:
            warn('Could not find service discovery service with id {svc}: {e}', svc=repr(service_id), e=e)
            return None


class DiscoveryServiceNamespace:
    services: List[DiscoveryServiceColor]
    cache_load_time: Optional[datetime.datetime]

    def __init__(
            self,
            namespace_port: Optional[int],
            namespace_id: str,
            namespace_arn: Optional[str],
            namespace_name: Optional[str],
    ) -> None:
        self.namespace_id = namespace_id
        self.namespace_port = namespace_port
        self.namespace_arn = namespace_arn
        self.namespace_name = namespace_name

        self.services = []
        self.cache_load_time = None

    # TODO move this up a level, and run "list_services" with a list of namespaces, and Condition 'IN'.
    def load_services(self, refresh_cache: bool) -> None:
        if skip_reload(self.cache_load_time, refresh_cache):
            return  # pragma: no cover

        # API INVOCATIONS: namespace_count * (1 + floor(this_namespace_service_color_count / 100))
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
    def from_resp(port: Optional[int], resp: Dict[str, Any]) -> 'DiscoveryServiceNamespace':
        if 'Namespace' in resp:
            resp = dt_dict(resp, 'Namespace')
        namespace_id = dt_str(resp, 'Id')
        namespace_arn = dt_str(resp, 'Arn')
        namespace_name = dt_str(resp, 'Name')
        # namespace_type = dt_str(resp, 'Type')
        # skip Description
        # hosted_zone_id = dt_opt_str(resp, 'Properties', 'DnsProperties', 'HostedZoneId')
        # http_name = dt_opt_str(resp, 'Properties', 'HttpProperties', 'HttpName')
        # service_count = dt_int(resp, 'ServiceCount')
        return DiscoveryServiceNamespace(
            namespace_port=port,
            namespace_id=namespace_id,
            namespace_arn=namespace_arn,
            namespace_name=namespace_name,
        )

    @staticmethod
    def load_namespaces(namespace_ports: Dict[str, Optional[int]]) -> List['DiscoveryServiceNamespace']:
        """
        Loads the service discovery namespaces requested.

        Namespaces can either be ARNs (prefixed with 'arn:', which is the standard), IDs
        (which you must explicitly prefix with 'id:'), or the namespace name.
        """

        ret: List['DiscoveryServiceNamespace'] = []
        client = get_servicediscovery_client()

        # Find namespace IDs.
        # ARNs are in the form 'arn:aws:servicediscovery:(region):(account):namespace/(namespace)'
        # Namespace IDs match 'ns-[a-z0-9]{16}', it looks like.
        # Namespace IDs, however, can very easily overlap the name, so if the user prepends a namespace id
        # with 'id:', then we use that as the explicit trigger.
        # Anything that doesn't match these will need to go into the list_namespaces for a long search.
        # That should be avoided, because it adds one additional Cloud Map service call *per loop*,
        # which can be costly over a month of continual usage.

        remaining_ports: Dict[str, Optional[int]] = {}
        for name, port in namespace_ports.items():
            pname = name.strip()
            arn_match = NAMESPACE_ARN_PATTERN.match(pname)
            if arn_match:
                # it looks like a valid arn... maybe.  Extract the namespace.
                ret.append(DiscoveryServiceNamespace(port, arn_match.group(1), pname, None))
            elif pname.startswith('id:'):
                ret.append(DiscoveryServiceNamespace(port, pname[3:], None, None))
            else:
                remaining_ports[name] = port

        if remaining_ports:
            # API INVOCATIONS: 1 + floor(namespace_count / 100)
            paginator = client.get_paginator('list_namespaces')
            for page in perform_client_request(lambda: list(paginator.paginate())):
                for raw in dt_list_dict(page, 'Namespaces'):
                    ns = DiscoveryServiceNamespace.from_resp(-1, raw)
                    if ns.namespace_id in remaining_ports:
                        del remaining_ports[ns.namespace_id]
                        ns.namespace_port = namespace_ports[ns.namespace_id]
                        ret.append(ns)
                    elif ns.namespace_arn in remaining_ports:
                        del remaining_ports[ns.namespace_arn]
                        ns.namespace_port = namespace_ports[ns.namespace_arn]
                        ret.append(ns)
                    elif ns.namespace_name in remaining_ports:
                        del remaining_ports[ns.namespace_name]
                        ns.namespace_port = namespace_ports[ns.namespace_name]
                        ret.append(ns)
        return ret


# ---------------------------------------------------------------------------
CLIENTS: Dict[str, object] = {}


def get_servicediscovery_client() -> Any:
    client_name = 'servicediscovery'
    if client_name not in CLIENTS:
        region = os.environ.get('AWS_REGION', None)
        profile = os.environ.get('AWS_PROFILE', None)
        session = boto3.session.Session(
            region_name=region,  # type: ignore
            profile_name=profile,  # type: ignore
        )
        CLIENTS[client_name] = session.client('servicediscovery', config=Config(
            max_pool_connections=1,
            retries=dict(max_attempts=2)
        ))
    return CLIENTS[client_name]


def perform_client_request(cmd: Callable[..., T], *vargs: Any, **kv_args: Any) -> T:
    throttle_err = None
    for retry_count in range(MAX_RETRY_COUNT):
        # Recommended exponential back-off rate.
        # https://docs.aws.amazon.com/AWSEC2/latest/APIReference/query-api-troubleshooting.html#api-request-rate
        # wait for (2^retries * 100) milliseconds
        # print("Try {0} after {1} seconds".format(retry_count + 1, (2 ** retry_count) / 10))
        time.sleep((2 ** retry_count) / 10)
        try:
            return cmd(*vargs, **kv_args)
        except ClientError as err:
            # See bug #1
            code = dt_opt_str(err.response, 'Error', 'Code')
            if code in ('RequestLimitExceeded', 'ThrottlingException',):
                # print("Throttled response.  Trying again.")
                throttle_err = err
                continue
            raise err
    raise throttle_err or Exception('throttled requests to ' + str(cmd))


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


# ---------------------------------------------------------------------------
def skip_reload(cache_load_time: Optional[datetime.datetime], refresh_cache: bool) -> bool:
    if not cache_load_time or refresh_cache:
        return False
    return datetime.datetime.now() - cache_load_time < REQUIRE_REFRESH_LIMIT
