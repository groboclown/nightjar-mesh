# Discovery Map Implementation: AWS ECS Task Tags

## Usage

In the Nightjar container that uses this discovery map, set the environment variables, in addition to the [standard settings](standard-usage.md):

```bash
DISCOVERY_MAP_EXEC="python3 -m nightjar_dm_aws_ecs_tags"
NJ_DMECS_AWS_CLUSTERS=comma,separated,list,of,aws,cluster,names
```

Details:

* `NJ_DMECS_AWS_CLUSTERS` - comma-separated list of cluster names to scan for ECS tasks that are considered for inclusion in the mesh.  If not given, then it scans the `default` cluster.


Additionally, the extension point uses the [standard Amazon account settings](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables).  
