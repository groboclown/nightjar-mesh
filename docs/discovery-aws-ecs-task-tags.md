# Discovery Map Implementation: AWS ECS Task Tags

## Usage

In the Nightjar container that uses this discovery map, set these environment variables, in addition to the [standard settings](standard-usage.md):

```bash
DISCOVERY_MAP_EXEC="python3 -m nightjar_dm_aws_ecs_tags"
NJ_DMECS_AWS_CLUSTERS=comma,separated,list,of,aws,cluster,names
NJ_DMECS_REQUIRED_TAG=tag_name
NJ_DMECS_REQUIRED_TAG_VALUE=tag_value
```


Details:

* `NJ_DMECS_AWS_CLUSTERS` - comma-separated list of ECS cluster names to scan for ECS tasks that are considered for inclusion in the mesh.  If not given, then it scans the `default` cluster.
* `NJ_DMECS_REQUIRED_TAG` - if given, then only ECS tasks with this tag name are considered part of the mesh.  This allows having a cluster with daemon tasks or any number of other tasks running that are filtered out of the mesh discovery.
* `NJ_DMECS_REQUIRED_TAG_VALUE` - if given and the `NJ_DMECS_REQUIRED_TAG` is given, then tasks must have this tag name equal to this tag value to be considered in the mesh.  Without the value but with the tag name, any task that has the tag name, regardless of its value, is considered part of the mesh.

Additionally, the extension point uses the [standard Amazon account settings](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables).  


## Configuring Each Service

Each ECS service must define its own nightjar configuration through the use of taskdef tags, task tags, taskdef container environment variables, and container overridden environment variables.  Due to the way AWS manages these, you can alter at runtime the tags, but the environment variable changes requires redeploying the containers.

There should be at most one service-color per taskdef.  If you are going to make runtime modifications to the tags, then do so through the task-def tags.  Modifying through the individual task tags will either be ignored or modify the entire service-color tasks.  This is because service-colors are considered a whole, and are not broken up by task.

Each service must define these environment variables or tags:

* `NJ_PROXY_MODE` - set to `SERVICE`.
* `NJ_SERVICE` - name of the service
* `NJ_COLOR` - name of the service's color
* `NJ_NAMESPACE` - name of the namespace the service belongs to.
* `NJ_PROTOCOL` - the http protocol that it listens to; this is optional.  If it is set to `HTTP2`, then the Envoy configuration uses that, otherwise it defaults to `HTTP1.1`.
* `NJ_ROUTE_(index)` - where `(index)` is any integer.  The value here is highly dependent upon the first character of the value:
    * `{` - this value is parsed as a JSON representation of the route information, as described in the [discovery-map-schema.yaml](../schema/discovery-map-schema.yaml).  This allows for full configuration.
    * `!` - the value after the leading `!` is a `prefix` and/or `exact` path that is internal to the namespace.  The gateway will not forward requests to this path, and other namespaces will not be able to reach this path.  If the value does not end with a '/', then it is considered both `prefix` and `exact`: if the value is `!/foo`, that routes to exactly `/foo` are forwarded, as are any path below `/foo/`.  If it ends with a `/`, then it is considered only a `prefix`.
    * `+` - the value after the leading `+` is a `prefix` and `exact` path that is public.
    * Any other value is treated like a public `prefix` and/or `exact` path.
* `NJ_ROUTE_PORT_(index)` - where `(index)` is associated with the corresponding `NJ_ROUTE_(index)` value.  Use this if the container listens to several ports, and this specific route listens on a specific port.  If the container listens to the same port on different bound IPs, then you can use a value of `(bound_ip):(port)`.
* `NJ_ROUTE_WEIGHT_(index)` - where `(index)` is associated with the corresponding `NJ_ROUTE_(index)` value.  Assigns a weight to the route, which must be a positive integer.  Default is `1`.
* `NJ_ROUTE_PORT` - the default port that accepts route traffic.  To override for a specific route, use `NJ_ROUTE_PORT_(index)`.  If not given, then the extension will make a best-effort to find a published port for the container.  If the container listens on several ports but only one for incoming route traffic, you should specify this variable.  If the container listens to the same port on different bound IPs, then you can use a value of `(bound_ip):(port)`.
* `NJ_NAMESPACE_PORT_(index)` - where `(index)` is any integer.  The value is of the form `(namespace):(port)`.  This is the envoy host's listening port to redirect requests to the given namespace.


## Configuring Gateways

Gateways are configured similar to ECS services, but with these required environment variables or tags:

* `NJ_PROXY_MODE` - set to `GATEWAY`.
* `NJ_NAMESPACE` - namespace for which the gateway will route traffic.
* `NJ_PREFER_GATEWAY` - set to a true value (e.g. `true`) to have mesh traffic prefer to go through the gateway, rather than direct to each service.  This defaults to `false`.
* `NJ_PROTOCOL` - the http protocol that the Envoy proxy uses.  If not specified, it defaults to `HTTP1.1`.
* `NJ_ROUTE_PORT` - the listening port for the gateway.  If not given, then the extension will make a best-effort to find a published port for the container.  If the container listens on several ports but only one for incoming route traffic, you should specify this variable.  If the container listens to the same port on different bound IPs, then you can use a value of `(bound_ip):(port)`.
