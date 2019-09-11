# Equivalent AWS CLI Commands

The flow of Nightjar for discovering information can be simulated through running commands in the AWS CLI.


## Get a List of ECS Services

Returns the list of service ARNs.  Each service can have multiple tasks.

```bash
aws ecs list-services \
    --cluster $CLUSTER_NAME
```

## Get a List of ECS Tasks Running in an ECS Service

Returns the list of task ARNs.  Each task is the equivalent to a Docker container.

```bash
aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_ARN
```


## Get Load Balancers and Port Mapping for a List of ECS Services

How to find the load balancers used by ECS service ARNs running in the same cluster.

```bash
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_ARN_1 $SERVICE_ARN_2 ...
# Fetchs a list of services; each one may contain a "loadBalancers", which has attributes
# targetGroupArn, containerName, containerPort
aws elbv2 describe-target-groups \
    --target-group-arns $TARGET_GROUP_ARN_1 $TARGET_GROUP_ARN_2 ...
# This, along with the describe-services, maps the container, container port, VPC,
# and load balancer ARN.
aws elbv2 describe-load-balancers \
    --load-balancer-arns $LOAD_BALANCER_ARN_1 $LOAD_BALANCER_ARN_2 ...
# We now have a DNS name, load balancer name, subnets, and hosted zone ID
# For each one of the load balancers, we can find the full mapping to the target groups.
aws elbv2 describe-listeners \
    --load-balancer-arn $LOAD_BALANCER_ARN_1
# Now we have, for each target group, the load balancer DNS name, the load
# balancer port and the mapped-to container name and port.
```


## Look up Route 53 DNS Aliases

Given a DNS alias name, we'll need to get the zone ID

```bash
aws route53 list-hosted-zones
# This gives us the hosted zone IDs and the registered DNS name suffix, like "com.example."
aws route53 list-resource-record-sets --hosted-zone-id $ZONE_ID
# This returns all the records.  The "Type": "A" and "Type": "CNAME" are the ones
# we usually care about, and they have an "AliasTarget" that includes the "DNSName".
```
