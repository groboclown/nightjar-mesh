# Nightjar Examples

This contains examples for using nightjar in various situations.


## Local Testing

[simple-mesh](simple-mesh/README.md)

This tree shows how nightjar works by running it entirely from your computer, without using any cloud resources.

This demonstrates the most basic way to use nightjar by setting up a simple service that responds to a path, and can forward on to other services.


## AWS Elastic Cloud Service

[standalone-aws-ecs-tags](standalone-aws-ecs-tags/README.md)

This example runs nightjar inside an ECS cluster, and uses tags and environment variables on the running containers to determine the mesh setup.

This creates a cluster and an elastic load balancer, and uses ECR, so be aware of AWS charges to your account.
