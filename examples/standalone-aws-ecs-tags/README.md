# Example CloudFormation Templates

Here you will find example CloudFormation template files that construct an ECS configuration that uses a Nightjar container loaded into the configuration.

You should carefully review the templates to ensure:

1. You understand the cost implications to running it.
1. You understand what security access you're granting.

Where possible, the security items are noted.

## Docker Images in ECR

This template requires uploading into ECR two images.

The first one is the `ServiceImage`, which is created by running:

```bash
$ docker build -t local/service-key-forward ../simple-mesh/service-key-forward
```

That's the simple service used in the local example.  It's just as useful here.

The next one is a nightjar stand-alone instance configured for internally stored 

## Configuration Parameters

The CloudFormation template takes these parameters.

