# General Documentation

## Introduction Documents

The top level [read-me](../README.md) is a great place to get acquainted with Nightjar, and to learn the terminology used (or attempted to be used) throughout the rest of the documentation and source code.

[Execution modes](execution-modes.md) describes details into the different ways you can deploy Nightjar into your environment.

The [simple mesh example](../examples/simple-mesh/README.md) is also a good introduction to using Nightjar while staying within your local computer.

## More Details

[Templates](templates.md) describes the templates document, and how Nightjar matches up services and gateways to a template.  It also describes the data format that Nightjar transforms the discovery-map to use with the templates.


## Usage Details

[Extension points](extension-points.md) describes how the extension points work, and what's expected of them.

After that, you should look into finding the right extension point for your situation.

* Standard Usage - most extension points require the [standard usage](standard-usage.md) guide to be followed.
* Discovery Map extension points create a discovery-map document based on a scan of the environment.
    * [AWS ECS Tags](discovery-aws-ecs-task-tags.md) uses ECS environment variables and resource tags to describe the mesh.
    * [AWS Cloud Map](discovery-aws-cloudmap.md) (in progress) uses AWS Cloud Map to describe the mesh.
* Data Store extension points store and retrieve documents, and can be used as a discovery-map by fetching it as a document.
    * [Local storage](store-local.md) for simple file-based approaches.
    * [AWS S3](store-aws-s3.md) keeps the files in S3.


## Older Cruft

Then there's older documentation that still needs to be sorted out.

* [standalone-deployment-model](standalone-deployment-model.md)
* [centralized-deployment-model](centralized-deployment-model.md)
