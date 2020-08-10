# Example CloudFormation Templates

*In Progress.  This is expected to start with a single mesh, expand to include a central discovery-map creator, then have multiple namespaces with their own gateways.*

Here you will find example CloudFormation template files that construct an ECS configuration that uses a Nightjar container loaded into the configuration.  Nightjar scans the ECS cluster for service members, and extracts templates from S3.

You should carefully review the templates to ensure:

1. You understand the cost implications to running it.
1. You understand what security access you're granting.

Where possible, the security items are noted.  The template attempts to keep the setup secure within your VPC, but you should still review it for cost and security concerns.

For this example, you will need:

* An AWS account.
* The AWS command line tool installed.
* Docker installed.
* Your AWS ECR account registered through Docker (to allow pushing images into ECR).

This document assumes:

* Your AWS account ID is `123456789012`.  Hopefully, this isn't actually your account number.
* Your AWS region is `us-west-2`.
* You setup your local AWS credentials using the profile name `my-aws-profile`.
* Your AWS S3 bucket for storing the Nightjar files is `my-nightjar-bucket`.  Further, the documents are stored in a sub-path called `nightjar-data/store`


## Initial Setup

Because this is getting a cluster running in AWS, the setup is always non-trivial.

### Docker Images in ECR

This template requires uploading into ECR three images.

The first one is the `ServiceImage`, which is created by running:

```bash
$ docker build -t local/service-key-forward ../simple-mesh/service-key-forward
```

That's the simple service used in the local example.  It's just as useful here.

The next two are the nightjar stand-alone and central images.  We'll store the templates in S3, so we can use the Nightjar containers as-is.

```bash
$ docker build -t local/nightjar-standalone -f ../../src/Dockerfile.envoy-standalone ../../src
$ docker build -t local/nightjar-central -f ../../src/Dockerfile.envoy-central ../../src
```

All of these need to be deployed into ECR, which means you'll also need to create a repository there for them.  You can change these repository names to suit your needs, but they'll be referenced by these names in this document.  Again, read this carefully, and use your particular account and region settings as necessary.

```bash
$ aws ecr --region us-west-2 create-repository --repository-name nightjar/service-key-forward
$ docker tag local/service-key-forward 123456789012.dkr.ecr.us-west-2.amazonaws.com/nightjar/service-key-forward
$ docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/nightjar/service-key-forward

$ aws ecr --region us-west-2 create-repository --repository-name nightjar/nightjar-standalone
$ docker tag local/nightjar-standalone 123456789012.dkr.ecr.us-west-2.amazonaws.com/nightjar/nightjar-standalone
$ docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/nightjar/nightjar-standalone

$ aws ecr --region us-west-2 create-repository --repository-name nightjar/nightjar-central
$ docker tag local/nightjar-central 123456789012.dkr.ecr.us-west-2.amazonaws.com/nightjar/nightjar-central
$ docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/nightjar/nightjar-central
```

### Templates in S3

The templates are managed by the [aws s3 data store](../../docs/store-aws-s3.md).  This uses an internal method to construct the storage to allow for nearly atomic operations.  Fortunately, the [`template-manager.sh`](../../docs/templates.md) script can help push these out to S3.

First, we'll create a local configuration that the template manager will use to know about the S3 bucket.  Create the file named `local-data-store-profiles.ini`, which looks like the following example (remember to replace values with your local configuration):

```ini
[default]
DATA_STORE_EXEC = python3 -m nightjar_ds_aws_s3
NJ_DSS3_BUCKET = my-nightjar-bucket
NJ_DSS3_BASE_PATH = nightjar-data/store
NJ_DSS3_MAX_DOCUMENT_SIZE_MB = 4
DEBUG=true

AWS_PROFILE=my-aws-profile
AWS_REGION=us-west-2
```

Now, we can upload the dynamic Envoy templates into our S3 data store, to create the default templates for both gateway and services:

```bash
$ ../../src/template-manager.sh \
    --file templates/envoy-config.yaml.mustache --purpose envoy-config.yaml \
    --category gateway push
$ ../../src/template-manager.sh \
    --file templates/cds.yaml.mustache --purpose cds.yaml \
    --category gateway push
$ ../../src/template-manager.sh \
    --file templates/lds.yaml.mustache --purpose lds.yaml \
    --category gateway push
$ ../../src/template-manager.sh \
    --file templates/envoy-config.yaml.mustache --purpose envoy-config.yaml \
    --category service push
$ ../../src/template-manager.sh \
    --file templates/cds.yaml.mustache --purpose cds.yaml \
    --category service push
$ ../../src/template-manager.sh \
    --file templates/lds.yaml.mustache --purpose lds.yaml \
    --category service push
```

First time template deployment can be a bit cumbersome; the tool was written around day-to-day maintenance of existing templates.


### Launch the Template and Configuration Parameters

When you launch the CloudFormation template, you will need to fill in the parameters.  The parameters are, for the most part, self-documenting.  The blank items will require you to fill them in, and the other values have sensible defaults, but you can change these to suit your needs. 


## Interacting with the Deployment

The template constructed a VPC-private load balancer that directs traffic on port 80 to the nightjar gateway container.  You can view the CFT resource description to find the name of the load balancer, then cross-reference that with the EC2 description of the load balancer to get the load balancer's DNS.

For this document's purposes, let's say the DNS is `internal-night-Gatew-1234-5678.us-west-2.elb.amazonaws.com`.  We can then make some requests:

```bash
$ curl http://internal-night-Gatew-1234-5678.us-west-2.elb.amazonaws.com/key/tuna
{"value":"tuna-ahi"}
$ curl http://internal-night-Gatew-1234-5678.us-west-2.elb.amazonaws.com/key/tuna
{"value":"tuna-blue"}
$ curl http://internal-night-Gatew-1234-5678.us-west-2.elb.amazonaws.com/forward/tuna
{"value":"tuna-blue"}
```

The cloudformation template was constructed such that the routing weight could be dynamic by placing that attribute on the task definition.  You can then modify the task definitions to change the tagged weight for each route.

Additionally, you can log into each EC2 instance in the auto-scaling group and inspect the running docker containers.  You will find the generated Envoy configuration files in the container named `ecs-yummy-tuna-ahi-12-nightjar-abcdef0123456` (or a similar name) - the "-nightjar-" in the name indicates it's the side-loaded container - in the `/tmp/envoy` directory.  Changing the tagged weights or S3 templates will be reflected in this directory.  *This is the inherent transparency that Nightjar gives the running environment - you can see exactly what Envoy is using.*


## Running With A Centralized Deployment Scheme

The previous example has each service discover the mesh independently.  In some cases, this can add extra CPU usage to your containers which you may not want, or it can add a large number of extra AWS requests that might cause throttling or extra costs.

To avoid this, but keep much of the same dynamic behavior, we can use a central discovery service that periodically performs the discovery and uploads the discovery-map into S3, which each of the nightjar sidecar containers pull.

You'll find these updates in [`01-ec2-mesh-central.yaml`](01-ec2-mesh-central.yaml).  This introduces a new, central service and task definition which manages the creation of the discovery map.  The other services are changed to just pull the discovery map from the S3 data store.  As a result of this change, now only the central container needs the ECS API access.

You can *update* the previous cloudformation template to the new version to see the changes.
