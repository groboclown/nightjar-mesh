# All About Templates

Templates are accessed through a [data store](extension-points.md#data-store) as a single JSON document, which must conform to a [JSON schema](../schema/templates-schema.yaml).


## What Can Templates Do?

Templates are files that are made available for the Envoy proxy to use in its configuration.

They are processed as [mustache templates](https://mustache.github.io/), using input from the [proxy-input schema](../schema/proxy-input-schema.yaml), which itself is a processed version of the [discovery-map data](../schema/discovery-map-schema.yaml).

The templates can have any purpose you want.  Generally, these should be to configure the Envoy proxy, but they could also be used to generate any kind of static file.  For example, it could generate an HTML report that the Envoy proxy has a static file route for.

## Matching Containers to Templates

Each gateway and service-color uses a collection of templates which are turned into many files for the Envoy proxy.  The [standalone container](entry-standalone.md) figures out the right collection of templates based on the settings for the current container.


## Managing Templates

Some data stores have particular ways to manage the template document.  The [template manager](../src/py-tool-template-manager) tool helps to manage the document, and individual templates within that document.

You can easily run the tool through the script [`template-manager.sh`](../src/template-manager.sh).

**Windows Warning** If you are running on Windows and the template manager reports problems running the data store extension point, then you've run into a known issue with the Python library for parsing commands.  Your alternative is to run the template manager from within a container.

To use the template manager, you first need to create a configuration file that describes the runtime environment for the data store executable.  For example, if using the [AWS S3 data store](store-aws-s3.md), you may configure it like this:

```ini
[s3]
DATA_STORE_EXEC = python3 -m nightjar_ds_aws_s3
NJ_DSS3_BUCKET = my-s3-bucket-name
NJ_DSS3_BASE_PATH = path/in/s3/bucket
NJ_DSS3_MAX_DOCUMENT_SIZE_MB = 4
AWS_PROFILE = my-aws-profile
```

The section (here, `s3`) is the *profile name*.  You may have multiple of these per configuration to easily switch between different setups.

To list out the current templates, you can run:

```bash
$ src/template-manager.sh --profile s3 list
```

You can view a template, here it's the service-color "s1-c1" in the "n1" namespace:

```bash
$ src/template-manager.sh --profile s3 --file - --category service --namespace n1 --service s1 --color c1 --purpose envoy.config.yaml pull 
```

You can upload templates to the data store, too.  In this example, it's the gateway for the 'n1' namespace:

```bash
$ src/template-manager.sh --profile s3 --file envoy.config.yaml --category service --namespace n1 --purpose envoy.config.yaml push
```
